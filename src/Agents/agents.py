from src.Tools.tools import fetch_url

def research_agent(state):
    user_input = state["input"]
    if "http" in user_input:
        state["steps"].append("Research: fetching URL")
        state["data"] = fetch_url(user_input)
    else:
        state["steps"].append("Research: calculating expression")
    return state

def Summarization_agent(state):
    data = state.get("data", "")
    if data and "Error" not in data:
        state["steps"].append("Summarization: summarizing data")
        state["summary"] = data[:200]  # Simple summarization by taking the first 200 characters
    else:
        state["steps"].append("Summarization: no data to summarize")
    return state

def Reviewer_agent(state):
    summary = state.get("summary", "")
    if summary and "Error" not in summary:
        state["steps"].append("Reviewer: reviewing summary")
        state["review"] = f"Review of summary: {summary[:100]}"  # Simple review by taking the first 100 characters
    else:
        state["steps"].append("Reviewer: no summary to review")
        state["output"] = "No summary available for review" 
    return state