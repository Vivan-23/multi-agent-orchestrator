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
    
def chunk_text(text: str, size: int = 200):
    try:
        return [text[i:i+size] for i in range(0, len(text), size)]
    except:
        return []

def deduplicate(data: list):
    try:
        return list(set(data))
    except:
        return data

def vector_search(texts, query):
    try:
        if not texts:
            return []

        # Mock embeddings (random vectors)
        vectors = np.random.rand(len(texts), 5).astype("float32")

        index = faiss.IndexFlatL2(5)
        index.add(vectors)

        q = np.random.rand(1, 5).astype("float32")

        _, I = index.search(q, k=min(3, len(texts)))

        return [texts[i] for i in I[0]]
    except:
        return texts[:3]


def execute_code(code: str):
    try:
        exec(code, {"__builtins__": {}})
        return "Code executed safely"
    except Exception as e:
        return f"Execution failed: {str(e)}"