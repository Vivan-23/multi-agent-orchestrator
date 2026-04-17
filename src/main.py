from fastapi import FastAPI
from fastapi import FastAPI, HTTPException
from urllib.parse import urlparse
from src.Core.orchestrator import run_pipeline
app = FastAPI()

def validate_input(user_input: str):
    if not user_input:
        raise HTTPException(status_code=400, detail="Input cannot be empty")

    # limit size
    if len(user_input) > 500:
        raise HTTPException(status_code=400, detail="Input too long")

    # basic URL validation
    if "http" in user_input:
        parsed = urlparse(user_input)
        if not parsed.scheme or not parsed.netloc:
            raise HTTPException(status_code=400, detail="Invalid URL")

    return user_input

@app.post("/run")
def run(data:dict):
    user_input = data.get("input", "")
    user_input = validate_input(user_input) #security check
    return run_pipeline(input=user_input)