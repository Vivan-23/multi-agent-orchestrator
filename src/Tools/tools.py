import requests
from datetime import datetime
from bs4 import BeautifulSoup
import requests

def get_current_time():
    """returns the current time in a human-readable format"""
    return datetime.now().strftime("%Y-%m-%d, %H:%M:%S")

import requests



def fetch_url(url: str):
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
    
def calculator(expression):
    try:
        result = eval(expression)
        return result
    except Exception as e:
        return f"Error: {str(e)}"