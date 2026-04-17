from fastapi import FastAPI
from src.Core.orchestrator import run_pipeline

app = FastAPI()


@app.get("/")
def home():
    return {"message": "LangGraph Agent Running 🚀"}


@app.post("/run")
def run(data: dict):
    user_input = data.get("input", "")
    return run_pipeline(user_input)