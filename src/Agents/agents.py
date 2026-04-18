from src.Tools.tools import (
    analyze_domain,
    find_subdomains,
    scan_endpoints,
    fetch_url,
    deduplicate
)
from src.Core.llm import generate_report
import json
from src.Core.logger import log_event


# 🔍 RECON AGENT
def recon_agent(state):
    run_id = state["run_id"]

    try:
        log_event("recon", "start", "running", run_id)

        domain = state["input"].replace("https://", "").replace("http://", "").split("/")[0]

        domain_info = analyze_domain(domain)
        subdomains = find_subdomains(domain)
        endpoints = scan_endpoints(domain)
        homepage = fetch_url(f"https://{domain}")

        state["data"] = {
            "domain_info": domain_info,
            "subdomains": subdomains,
            "endpoints": endpoints,
            "raw_text": homepage
        }

        state["steps"].append("Recon completed")

        log_event("recon", "complete", "success", run_id)
        return state

    except Exception as e:
        log_event("recon", "failed", "error", run_id, str(e))
        state["errors"] += 1
        return state


# ⚙️ PROCESSING AGENT
def processing_agent(state):
    run_id = state["run_id"]

    try:
        log_event("processing", "start", "running", run_id)

        data = state["data"]

        data["subdomains"] = deduplicate(data["subdomains"])
        data["endpoints"] = deduplicate(data["endpoints"])

        state["data"] = data
        state["steps"].append("Processing completed")

        log_event("processing", "complete", "success", run_id)
        return state

    except Exception as e:
        log_event("processing", "failed", "error", run_id, str(e))
        state["errors"] += 1
        return state


# 🧠 REPORT AGENT (no LLM yet)
def report_agent(state):
    run_id = state["run_id"]
    model = state.get("model", "llama-3.1-8b-instant")

    log_event("report", "start", "running", run_id)

    data = state["data"] 
    domain = data["domain_info"]["domain"]

    prompt = f"""
You are given reconnaissance data.

Domain Info: {data["domain_info"]}
Subdomains: {data["subdomains"]}
Endpoints: {data["endpoints"]}
Content: {data["raw_text"][:500]}

Task:
Return a JSON object with:
- domain
- summary
- subdomains
- endpoints
- technologies
- insights
- citations

Return ONLY JSON.
"""

    llm_output = generate_report(prompt, model)

    try:
        parsed = json.loads(llm_output)
    except:
        parsed = {
            "domain": domain,
            "summary": llm_output,
            "subdomains": data["subdomains"],
            "endpoints": data["endpoints"],
            "technologies": data["domain_info"]["technologies"],
            "insights": ["Fallback due to parsing"],
            "citations": [f"https://{domain}"]
        }
    print("MODEL:", model)
    print("CALLING LLM...")
    state["output"] = parsed

    log_event("report", "complete", "success", run_id)
    return state