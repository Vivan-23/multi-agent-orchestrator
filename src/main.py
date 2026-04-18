from fastapi import FastAPI
from src.Core.orchestrator import run_pipeline

app = FastAPI()


@app.get("/")
def home():
    return {"message": "LangGraph Agent Running 🚀"}

@app.post("/run")
def run(data: dict):
    user_input = data.get("input", "")
    model = data.get("model", "mock-model")

    return run_pipeline(user_input, model)

@app.get("/runs")
def get_runs():
    try:
        with open("data/runs.json", "r") as f:
            return json.load(f)
    except:
        return []
    
@app.get("/logs")
def get_logs():
    try:
        with open("logs/run_logs.jsonl", "r") as f:
            return [line for line in f.readlines()]
    except:
        return []