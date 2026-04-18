import json
from datetime import datetime
import os

LOG_FILE = "logs/run_logs.jsonl"

# ensure logs folder exists
os.makedirs("logs", exist_ok=True)


def log_event(agent: str, step: str, status: str, run_id: str, error: str = None):
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "run_id": run_id,   # 🔥 important
        "agent": agent,
        "step": step,
        "status": status,
        "error": error
    }

    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(log_entry) + "\n")