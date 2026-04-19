import requests
from datetime import datetime
from bs4 import BeautifulSoup
import requests
from urllib.parse import urlparse
import faiss
import numpy as np
import socket
def get_current_time():
    """returns the current time in a human-readable format"""
    return datetime.now().strftime("%Y-%m-%d, %H:%M:%S")

def extract_base_domain(url: str):
    parsed = urlparse(url if "://" in url else "http://" + url)
    parts = parsed.netloc.split(".")
    return ".".join(parts[-2:])

def is_safe_url(url: str):
    parsed = urlparse(url)

    if parsed.scheme not in ["http", "https"]:
        return False

    if "localhost" in parsed.netloc or "127.0.0.1" in parsed.netloc:
        return False

    return True

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

def validate_subdomains(domain, candidates):
    real = []
    for sub in candidates:
        try:
            socket.gethostbyname(f"{sub}.{domain}")
            real.append(f"{sub}.{domain}")
        except socket.gaierror:
            pass
    return real

def find_subdomains(domain: str):
    candidates = [
        "admin", "dev", "api", "mail", "staging", "app",
        "portal", "dashboard", "beta", "test", "sandbox",
        "cdn", "auth", "login", "status", "cloud", "blog",
        "python", "js", "go", "hub", "console", "manage",
        "internal", "secure", "vpn", "remote", "git",
        "gitlab", "jenkins", "jira", "confluence", "grafana"
    ]

    return validate_subdomains(domain, candidates)
    
def detect_technologies(headers):
    techs = []
    server = headers.get("Server", "")
    powered = headers.get("X-Powered-By", "")
    if server: techs.append(server)
    if powered: techs.append(powered)
    return techs

def analyze_domain(domain: str):
    try:
        ip = socket.gethostbyname(domain)
    except:
        ip = "unknown"
        
    techs = []
    try:
        res = requests.get(f"http://{domain}", timeout=5, headers={"User-Agent": "Mozilla/5.0"})
        techs = detect_technologies(res.headers)
    except:
        pass

    return {
        "domain": domain,
        "ip": ip,
        "hosting": "unknown",
        "technologies": techs
    }

def validate_endpoints(domain, candidates):
    real = []
    
    # first get the homepage response to detect catch-all
    try:
        home = requests.get(
            f"http://{domain}",
            timeout=3,
            allow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        home_content = home.text[:200]  # fingerprint of homepage
    except:
        home_content = ""

    for path in candidates:
        try:
            url = f"http://{domain}{path}"
            res = requests.get(
                url,
                timeout=3,
                allow_redirects=True,
                headers={"User-Agent": "Mozilla/5.0"}
            )

            # if response looks identical to homepage = catch-all redirect, skip
            if home_content and res.text[:200] == home_content:
                continue

            if res.status_code == 200:
                real.append({"url": url, "status": "open"})
            elif res.status_code == 403:
                real.append({"url": url, "status": "forbidden"})
            elif res.status_code in [301, 302]:
                location = res.headers.get("Location", "")
                if location.rstrip("/") in [
                    f"http://{domain}",
                    f"https://{domain}",
                    "/"
                ]:
                    continue  # catch-all redirect to homepage, skip
                real.append({"url": url, "status": "redirect"})

        except:
            pass

    return real

def scan_endpoints(domain: str):
    paths = [
        "/robots.txt", "/sitemap.xml", "/sitemap_index.xml",
        "/admin", "/admin/login", "/administrator",
        "/login", "/signin", "/signup", "/register",
        "/api", "/api/v1", "/api/v2", "/api/docs",
        "/dashboard", "/panel", "/console",
        "/auth", "/oauth", "/sso",
        "/internal", "/private", "/secret",
        "/.env", "/.git", "/config",
        "/swagger", "/swagger-ui", "/openapi.json",
        "/graphql", "/graphiql",
        "/health", "/status", "/ping",
        "/metrics", "/debug", "/trace",
        "/upload", "/uploads", "/files",
        "/backup", "/old", "/test",
        "/wp-admin", "/wp-login.php",  # wordpress
        "/phpmyadmin",                  # php
        "/server-status",               # apache
    ]
    return validate_endpoints(domain, paths)


def execute_code(code: str):
    try:
        result = subprocess.run(
            ["python", "-c", code],
            timeout=5,
            capture_output=True,
            text=True
        )
        return result.stdout or result.stderr
    except subprocess.TimeoutExpired:
        return "Error: timeout"
    except Exception as e:
        return f"Execution failed: {str(e)}"

def vector_search(query: str, documents: list):
    dim = 8
    index = faiss.IndexFlatL2(dim)
    vecs = np.random.rand(len(documents), dim).astype("float32")
    index.add(vecs)
    query_vec = np.random.rand(1, dim).astype("float32")
    _, indices = index.search(query_vec, k=min(3, len(documents)))
    return [documents[i] for i in indices[0]]