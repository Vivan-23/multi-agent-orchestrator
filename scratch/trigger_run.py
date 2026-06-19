import requests
import json

url = "http://localhost:8000/run"
payload = {
    "input": "https://qdrant.tech/documentation/overview/vector-search/",
    "model": "llama-3.3-70b-versatile"
}

print("Triggering run via API...")
try:
    response = requests.post(url, json=payload, timeout=90)
    print("Status Code:", response.status_code)
    if response.status_code == 200:
        data = response.json()
        print("Run complete!")
        print("Run ID:", data.get("run_id"))
        print("Model Used:", data.get("model_used"))
        print("Risk Level:", data.get("risk_level"))
        print("Summary:", data.get("output", {}).get("summary"))
        print("Metrics:", data.get("metrics"))
        
        # Now query the logs endpoint
        run_id = data.get("run_id")
        logs_url = f"http://localhost:8000/logs/{run_id}"
        logs_response = requests.get(logs_url)
        print("\nLogs:")
        for log in logs_response.json():
            print(f"[{log['timestamp']}] {log['agent']} - {log['event']} ({log['status']}): {log['message']}")
    else:
        print("Error response:", response.text)
except Exception as e:
    print("Error:", e)
