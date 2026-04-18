import requests
from datetime import datetime
from bs4 import BeautifulSoup
import requests
from urllib.parse import urlparse
import faiss
import numpy as np


def get_current_time():
    """returns the current time in a human-readable format"""
    return datetime.now().strftime("%Y-%m-%d, %H:%M:%S")

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

def find_subdomains(domain: str):
    return [
        f"api.{domain}",
        f"dev.{domain}",
        f"admin.{domain}"
    ]
    
def analyze_domain(domain: str):
    return {
        "domain": domain,
        "ip": "93.184.216.34",
        "hosting": "Example Hosting",
        "technologies": ["nginx", "react"]
    }

def scan_endpoints(domain: str):
    return [
        f"https://{domain}/login",
        f"https://{domain}/api",
        f"https://{domain}/dashboard"
    ]

def execute_code(code: str):
    try:
        exec(code, {"__builtins__": {}})
        return "Code executed safely"
    except Exception as e:
        return f"Execution failed: {str(e)}"