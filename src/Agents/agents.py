from src.Tools.tools import (
    fetch_url,
    chunk_text,deduplicate,
    vector_search
)


from src.Core.logger import log_event

def research_agent(state):
    try:
        log_event("research", "start", "running")

        url = state.get("input", "")
        text = fetch_url(url)
        chunks = chunk_text(text)

        state["data"] = chunks

        log_event("research", "complete", "success")
        return state

    except Exception as e:
        log_event("research", "failed", "error", str(e))
        state["errors"] += 1
        return state

def processing_agent(state):
    try:
        log_event("processing", "start", "running")

        data = deduplicate(state["data"])
        results = vector_search(data, state["input"])

        state["data"] = results

        log_event("processing", "complete", "success")
        return state

    except Exception as e:
        log_event("processing", "failed", "error", str(e))
        state["errors"] += 1
        return state

def synthesis_agent(state):
    try:
        log_event("synthesis", "start", "running")

        if not state["data"]:
            state["output"] = "No useful data found"
            return state

        combined = " ".join(state["data"])
        state["output"] = combined[:300]

        log_event("synthesis", "complete", "success")
        return state

    except Exception as e:
        log_event("synthesis", "failed", "error", str(e))
        state["errors"] += 1
        return state