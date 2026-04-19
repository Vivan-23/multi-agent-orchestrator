from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.Core.orchestrator import run_pipeline

import json
from src.Core.orchestrator import RUNS_FILE

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

@app.get("/")
def home():
    # Serve the frontend index.html on the root path
    return FileResponse("frontend/index.html")



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
            content = f.read().strip()
            runs = json.loads(content) if content else []

        return runs[-5:][::-1]   # last 5, newest first

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

# Mount the entire frontend directory for css, js, etc. MUST BE AT THE BOTTOM!
app.mount("/", StaticFiles(directory="frontend"), name="frontend")