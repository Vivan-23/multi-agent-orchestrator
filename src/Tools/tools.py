import requests
import time
import threading
import logging
from datetime import datetime
from functools import wraps
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import socket
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import ipaddress
import os
from dotenv import load_dotenv
logger = logging.getLogger(__name__)
model = None
load_dotenv()
def get_sentence_transformer():
    global model
    if model is None:
        model = SentenceTransformer("all-MiniLM-L6-v2")
    return model

def extract_base_domain(url: str) -> str:
    url = url.strip()
    parsed = urlparse(url if "://" in url else "http://" + url)
    netloc = parsed.netloc.split(":")[0]  # remove port if any
    parts = netloc.split(".")
    if len(parts) > 2:
        second_to_last = parts[-2]
        last = parts[-1]
        if second_to_last in ["co", "com", "net", "org", "gov", "edu"] and len(last) == 2:
            return ".".join(parts[-3:])
        return ".".join(parts[-2:])
    return ".".join(parts)


# ---------------------------------------------------------------------------
# Rate-limit decorator (token-bucket, thread-safe)
# ---------------------------------------------------------------------------
def rate_limit(max_calls: int = 5, period: float = 60.0):
    """Decorator that limits a function to *max_calls* invocations per
    *period* seconds.  Extra calls block until a token is available.
    """
    def decorator(fn):
        lock = threading.Lock()
        call_timestamps: list[float] = []

        @wraps(fn)
        def wrapper(*args, **kwargs):
            with lock:
                now = time.monotonic()
                # Purge timestamps older than the window
                while call_timestamps and call_timestamps[0] <= now - period:
                    call_timestamps.pop(0)

                if len(call_timestamps) >= max_calls:
                    sleep_for = period - (now - call_timestamps[0])
                    if sleep_for > 0:
                        logger.info(
                            "rate_limit: %s throttled — sleeping %.1fs",
                            fn.__name__, sleep_for,
                        )
                        lock.release()
                        time.sleep(sleep_for)
                        lock.acquire()
                        # Re-purge after sleeping
                        now = time.monotonic()
                        while call_timestamps and call_timestamps[0] <= now - period:
                            call_timestamps.pop(0)

                call_timestamps.append(time.monotonic())

            return fn(*args, **kwargs)

        # Expose internals for testing / introspection
        wrapper._rate_limit_max_calls = max_calls
        wrapper._rate_limit_period = period
        return wrapper
    return decorator

def vector_search(texts, query):
    t_model = get_sentence_transformer()
    embeddings = t_model.encode(texts)
    query_vec = t_model.encode([query])

    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(np.array(embeddings))

    _, I = index.search(np.array(query_vec), k=3)

    return [texts[i] for i in I[0]]

def get_current_time():
    """returns the current time in a human-readable format"""
    return datetime.now().strftime("%Y-%m-%d, %H:%M:%S")


BLOCKED_IP_RANGES = [
    ipaddress.ip_network("127.0.0.0/8"),      # loopback
    ipaddress.ip_network("10.0.0.0/8"),        # RFC1918
    ipaddress.ip_network("172.16.0.0/12"),     # RFC1918
    ipaddress.ip_network("192.168.0.0/16"),    # RFC1918
    ipaddress.ip_network("169.254.0.0/16"),    # cloud metadata (AWS/GCP/Azure)
    ipaddress.ip_network("0.0.0.0/8"),         # unspecified
    ipaddress.ip_network("::1/128"),           # IPv6 loopback
    ipaddress.ip_network("fe80::/10"),         # IPv6 link-local
    ipaddress.ip_network("fc00::/7"),          # IPv6 unique local
]

# Authorized scope — only probe domains the user explicitly authorized
AUTHORIZED_SCOPE = []  # populated per-run via set_scope()

def set_scope(domains: list):
    global AUTHORIZED_SCOPE
    AUTHORIZED_SCOPE = [d.lower().strip() for d in domains]

def is_in_scope(domain: str) -> bool:
    if not AUTHORIZED_SCOPE:
        return True  # no scope set = open (dev mode)
    domain = domain.lower().strip()
    return any(domain == s or domain.endswith("." + s) for s in AUTHORIZED_SCOPE)

def is_safe_url(url: str) -> bool:
    try:
        parsed = urlparse(url if "://" in url else "http://" + url)

        # scheme check
        if parsed.scheme not in ["http", "https"]:
            return False

        hostname = parsed.hostname
        if not hostname:
            return False

        # scope check
        if not is_in_scope(hostname):
            return False

        # resolve to IP and check ranges
        try:
            resolved_ip = socket.gethostbyname(hostname)
            ip_obj = ipaddress.ip_address(resolved_ip)
            for blocked in BLOCKED_IP_RANGES:
                if ip_obj in blocked:
                    return False
        except socket.gaierror:
            return False  # can't resolve = unsafe

        return True

    except Exception:
        return False

def fetch_url(url: str):
    if(is_safe_url(url) == False):
        return "Error: Unsafe URL. Only http and https URLs are allowed, and localhost is not allowed."
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=5)
        res.raise_for_status()

        soup = BeautifulSoup(res.text, "html.parser")

        # Extract readable text
        text = soup.get_text(separator=" ", strip=True)

        return text[:1000]

    except Exception as e:
        return f"Error: {str(e)}"
    

def deduplicate(data: list):
    try:
        return list(set(data))
    except:
        return data

# def find_subdomains(domain: str):
#     return [
#         f"api.{domain}",
#         f"dev.{domain}",
#         f"admin.{domain}"
#     ]
    
# def analyze_domain(domain: str):
#     return {
#         "domain": domain,
#         "ip": "93.184.216.34",
#         "hosting": "Example Hosting",
#         "technologies": ["nginx", "react"]
#     }

@rate_limit(max_calls=5, period=60.0)
def scan_endpoints(domain: str):
    return [
        f"https://{domain}/login",
        f"https://{domain}/api",
        f"https://{domain}/dashboard"
    ]
    
@rate_limit(max_calls=4, period=60)
def virustotal_scan(domain: str):
    url = f"https://www.virustotal.com/api/v3/domains/{domain}"
    api = os.getenv("VIRUSTOTAL_API_KEY")
    if api is None:
        return "Error: VIRUSTOTAL_API_KEY not found."
    try:
        headers = {
            "accept": "application/json",
            "x-apikey": api
        }
    
        response = requests.get(url, headers=headers)
        if response.status_code == 429:
            return "Error: Rate limit exceeded. Please try again later."
    
        response.raise_for_status()
        return response.json()  
    except Exception as e:
        return f"Error: {str(e)}"

@rate_limit(max_calls=4, period=60)
def virustotal_find_subdomains(domain: str):
    url = f"https://www.virustotal.com/api/v3/domains/{domain}/subdomains?limit=40"
    api = os.getenv("VIRUSTOTAL_API_KEY")
    if api is None:
        return "Error: VIRUSTOTAL_API_KEY not found."
    try:
        headers = {
            "accept": "application/json",
            "x-apikey": api
        }
    
        response = requests.get(url, headers=headers)
        if response.status_code == 429:
            return "Error: Rate limit exceeded. Please try again later."
        
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return f"Error: {str(e)}"
        
def find_subdomains(domain: str):
    result = virustotal_find_subdomains(domain)

    if isinstance(result, str) and result.startswith("Error"):
        # fallback to old behavior if VT fails
        return [f"api.{domain}", f"dev.{domain}", f"admin.{domain}"]

    try:
        subdomains = [item["id"] for item in result.get("data", [])]
        return subdomains if subdomains else [f"api.{domain}", f"dev.{domain}", f"admin.{domain}"]
    except Exception:
        return [f"api.{domain}", f"dev.{domain}", f"admin.{domain}"]


def analyze_domain(domain: str):
    try:
        ip = socket.gethostbyname(domain)
    except socket.gaierror:
        ip = "unknown"

    vt_result = virustotal_scan(domain)
    shodan_result = shodan_scan(ip) if ip != "unknown" else "Error: no IP"

    # defaults
    hosting = "unknown"
    technologies = []
    malicious_votes = 0
    harmless_votes = 0
    categories = []
    open_ports = []
    vulnerabilities = []

    # ---- VirusTotal extraction (you already have this logic, reuse it) ----
    if not (isinstance(vt_result, str) and vt_result.startswith("Error")):
        try:
            attrs = vt_result["data"]["attributes"]
            stats = attrs.get("last_analysis_stats", {})
            categories = list(attrs.get("categories", {}).values())
            hosting = attrs.get("registrar", "unknown")
            technologies = categories
            malicious_votes = stats.get("malicious", 0)
            harmless_votes = stats.get("harmless", 0)
        except Exception:
            pass

    if not (isinstance(shodan_result, str) and shodan_result.startswith("Error")):
        try:
            open_ports = shodan_result.get("ports", [])
            vulnerabilities = shodan_result.get("vulns", [])
            if hosting == "unknown":
                hosting = shodan_result.get("org") or shodan_result.get("isp") or "unknown"
        except Exception:
            pass
    return {
        "domain": domain,
        "ip": ip,
        "hosting": hosting,
        "technologies": technologies,
        "malicious_votes": malicious_votes,
        "harmless_votes": harmless_votes,
        "categories": categories,
        "open_ports": open_ports,
        "vulnerabilities": vulnerabilities
    }
@rate_limit(max_calls=4, period=60) 
def shodan_scan(ip_address: str):
    try:
        api = os.getenv("SHODAN_API_KEY")
        if api is None:
            return "Error: SHODAN_API_KEY not found."
        url = f"https://api.shodan.io/shodan/host/{ip_address}?key={api}"
        headers = {
            "accept": "application/json",
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 429:
            return "Error: Rate limit exceeded. Please try again later."
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return f"Error: {str(e)}"