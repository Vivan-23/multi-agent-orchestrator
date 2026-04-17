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


# runner function
def run_pipeline(user_input: str):
    return app_graph.invoke({
        "input": user_input,
        "steps": [],
        "data": [],
        "output": "",
        "errors": 0
    })