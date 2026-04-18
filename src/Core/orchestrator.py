from langgraph.graph import StateGraph
from src.Agents.agents import (
    recon_agent,
    processing_agent,
    report_agent
)

import uuid
from typing import TypedDict, List
import json
import os
RUNS_FILE = "data/runs.json"
os.makedirs("data", exist_ok=True)

def save_run(state):
    try:
        if not os.path.exists(RUNS_FILE):
            with open(RUNS_FILE, "w") as f:
                json.dump([], f)

        with open(RUNS_FILE, "r") as f:
            runs = json.load(f)

        runs.append(state)

        with open(RUNS_FILE, "w") as f:
            json.dump(runs, f, indent=2)

    except:
        pass
    
    
class State(TypedDict):
    input: str
    steps: List[str]
    data: dict   # ✅ FIXED
    output: dict # ✅ FIXED
    errors: int
    retries: int
    run_id: str
    model: str
    risk_level: str

def with_retry(agent_func, max_retries=2):
    def wrapper(state):
        attempts = 0

        while attempts < max_retries:
            try:
                return agent_func(state)
            except Exception as e:
                attempts += 1
                state["errors"] += 1
                state["steps"].append(f"Retry {attempts} for {agent_func.__name__}")

        state["output"] = f"Failed after {max_retries} retries"
        return state

    return wrapper

# build graph
graph = StateGraph(State)

# nodes
graph.add_node("recon", with_retry(recon_agent))
graph.add_node("processing", with_retry(processing_agent))
graph.add_node("report", with_retry(report_agent))

graph.set_entry_point("recon")
graph.add_edge("recon", "processing")
graph.add_edge("processing", "report")
# compile
app_graph = graph.compile()

def evaluate(state):
    steps_count = len(state["steps"])
    error_count = state["errors"]

    score = max(0, 10 - error_count)

    return {
        "steps_count": steps_count,
        "error_count": error_count,
        "eval_score": score
    }
    
    

def run_pipeline(user_input: str, model: str = "llama-3.1-8b-instant"):

    run_id = str(uuid.uuid4())  # 🔥 unique id

    state = app_graph.invoke({
        "input": user_input,
        "steps": [],
        "data": {},
        "output": {},
        "errors": 0,
        "retries": 0,
        "model": model,
        "run_id": run_id   # 👈 ADD THIS
        
    })

    state["metrics"] = evaluate(state)
    state["run_id"] = run_id

    save_run(state)

    return state