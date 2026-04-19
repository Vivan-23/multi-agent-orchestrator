from langgraph.graph import StateGraph
from src.Agents.agents import (
    recon_agent,
    processing_agent,
    report_agent
)
from src.Core.state import AgentState
import uuid
from typing import TypedDict, List
import json
import os
import time
from src.Core.llm import VALID_MODELS
import datetime

RUNS_FILE = "data/runs.json"
os.makedirs("data", exist_ok=True)

def save_run(state):
    try:
        runs = []
        if os.path.exists(RUNS_FILE):
            with open(RUNS_FILE, "r") as f:
                content = f.read().strip()
                if content:
                    runs = json.loads(content)

        runs.append(state)

        with open(RUNS_FILE, "w") as f:
            json.dump(runs, f, indent=2)

    except Exception as e:
        print(f"Error saving run: {e}")
    
    
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
        for attempt in range(max_retries):
            try:
                return agent_func(state)
            except Exception:
                state["errors"] += 1
                state["steps"].append(f"Retry {attempt+1} for {agent_func.__name__}")
                time.sleep(1 * (attempt + 1))  # backoff

        state["steps"].append(f"{agent_func.__name__} failed permanently")
        state["output"] = {"error": "Pipeline stopped due to repeated failure"}
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
    output = state.get("output", {})

    schema_valid = isinstance(output, dict) and "summary" in output
    unique_sources = len(set(output.get("citations", [])))
    tool_error_rate = state["errors"] / max(1, len(state["steps"]))

    score = 10
    if not schema_valid: score -= 3
    if unique_sources < 2: score -= 2
    if tool_error_rate > 0.3: score -= 2

    return {
        "steps_count": len(state["steps"]),
        "tool_error_rate": tool_error_rate,
        "schema_valid": schema_valid,
        "unique_sources": unique_sources,
        "eval_score": score*10
    }
    
    

def run_pipeline(user_input: str, model: str = "openai"):
    
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
    state["model_used"] = VALID_MODELS.get(state.get("model","openai"), VALID_MODELS["openai"])
    # state["timestamp"] = datetime.now().isoformat()

    save_run(state)

    return state