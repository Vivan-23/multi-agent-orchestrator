from langgraph.graph import StateGraph
from src.Agents.agents import (
    research_agent,
    processing_agent,
    synthesis_agent
)


from typing import TypedDict, List

class State(TypedDict):
    input: str
    steps: List[str]
    data: List[str]
    output: str
    errors: int
    retries : int

def with_retry(agent_func, max_retries=2):
    def wrapper(state):
        attempts = 0

        while attempts <= max_retries:
            try:
                return agent_func(state)
            except Exception as e:
                attempts += 1
                state["errors"] += 1
                state["steps"].append(f"Retry {attempts} for {agent_func.__name__}")

        state["output"] = f"Failed after {max_retries} retries"
        return state

    return wrapper

# wrap agents
research_node = with_retry(research_agent)
processing_node = with_retry(processing_agent)
synthesis_node = with_retry(synthesis_agent)

# build graph
graph = StateGraph(State)

# nodes
graph.add_node("research", research_agent)
graph.add_node("processing", processing_agent)
graph.add_node("synthesis", synthesis_agent)

# flow
graph.set_entry_point("research")
graph.add_edge("research", "processing")
graph.add_edge("processing", "synthesis")

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
    
    

# runner function
def run_pipeline(user_input: str):
    return app_graph.invoke({
        "input": user_input,
        "steps": [],
        "data": [],
        "output": "",
        "errors": 0,
        "retries": 0
    })
    
    state["metrics"] = evaluate(state)

    return state