from fastapi import FastAPI
from src.Core.orchestrator import run_pipeline

import json
from src.Core.orchestrator import RUNS_FILE
app = FastAPI()


@app.get("/")
def home():
    return {"message": "LangGraph Agent Running 🚀"}

@app.post("/run")
def run(data: dict):
    return run_pipeline(
        data.get("input", ""),
        data.get("model", "llama3-8b-8192")
    )


@app.get("/runs")
def get_runs():
    try:
        with open(RUNS_FILE, "r") as f:
            data = json.load(f)   # ✅ proper parsing
        return data
    except Exception as e:
        return {"error": str(e)}
    
@app.get("/logs/{run_id}")
def get_logs_by_run(run_id: str):
    try:
        with open("logs/run_logs.jsonl", "r") as f:
            logs = [json.loads(line) for line in f.readlines()]

        # ✅ SAFE ACCESS
        filtered = [
            log for log in logs 
            if log.get("run_id") == run_id
        ]

        return filtered

    except Exception as e:
        return {"error": str(e)}