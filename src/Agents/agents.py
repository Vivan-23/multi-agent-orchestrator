from src.Tools.tools import (
    fetch_url,
    chunk_text,deduplicate,
    vector_search
)


# 🔍 RESEARCH AGENT
def research_agent(state):
    url = state["input"]
    state["steps"].append("Research: fetching + parsing")

   
    text = fetch_url(url)
    chunks = chunk_text(text)

    state["data"] = chunks
    return state


# ⚙️ PROCESSING AGENT
def processing_agent(state):
    state["steps"].append("Processing: dedupe + retrieval")

    data = deduplicate(state["data"])
    results = vector_search(data, state["input"])

    state["data"] = results
    return state


# 🧠 SYNTHESIS AGENT
def synthesis_agent(state):
    state["steps"].append("Synthesis: generating output")

    if not state["data"]:
        state["output"] = "No useful data found"
        return state

    combined = " ".join(state["data"])
    state["output"] = combined[:300]

    return state