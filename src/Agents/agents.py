from src.Tools.tools import (
    analyze_domain,
    find_subdomains,
    scan_endpoints,
    fetch_url,
    deduplicate,
    extract_base_domain
)
from src.Core.llm import generate_report
import json
from src.Core.logger import log_event
from src.Tools.tools import set_scope

def recon_agent(state):
    run_id = state["run_id"]

    try:
        log_event("recon", "start", "running", run_id)
        state["steps"].append("Recon started")

        # 1. extract domain from input
        url = state["input"]
        if not url.startswith("http"):
            url = "http://" + url

        domain = url.replace("https://", "").replace("http://", "").split("/")[0]
        base_domain = extract_base_domain(url)

        # 2. set scope BEFORE any probing
        set_scope([base_domain])

        # 3. fetch homepage with fallback http/https
        homepage = fetch_url(url)
        if not homepage or homepage.startswith("Error"):
            https_url = f"https://{domain}"
            homepage = fetch_url(https_url)
        if not homepage or homepage.startswith("Error"):
            http_url = f"http://{domain}"
            homepage = fetch_url(http_url)

        # 4. run recon tools
        domain_info = analyze_domain(domain)
        subdomains = find_subdomains(base_domain)   # use base_domain not domain
        endpoints = scan_endpoints(domain)

        state["data"] = {
            "domain_info": domain_info,
            "subdomains": subdomains,
            "endpoints": endpoints,
            "raw_text": homepage or ""
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

def clean_llm_output(text: str):
    text = text.strip()

    # remove markdown ```json ``` if present
    if text.startswith("```"):
        text = text.split("```")[1]
    
    if text.endswith("```"):
        text = text[:-3]

    return text.strip()

# 🧠 REPORT AGENT (no LLM yet)
def report_agent(state):
    run_id = state["run_id"]
    model = state.get("model", "fast")

    log_event("report", "start", "running", run_id)

    data = state["data"] 
    domain = data["domain_info"]["domain"]

    prompt = f"""
You are a cybersecurity reconnaissance analyst. Your job is to analyze recon data and return structured intelligence.

---

RECON DATA:
- Domain Info: {data["domain_info"]}
- - Subdomains ({len(data["subdomains"])} total, showing first 10): {data["subdomains"][:]}
- Endpoints: {data["endpoints"]}
- Page Content (truncated): {data["raw_text"][:500]}

---

ANALYSIS RULES:

1. INSIGHTS (3–5 only):
   - Must be analytical, not descriptive
   - Must reference specific evidence (subdomains, endpoints, patterns)
   - BAD: "Has a login page"
   - GOOD: "Exposed /auth endpoint combined with admin subdomain suggests authentication surface is externally reachable"

2. RISK LEVEL (pick one):
   - "low"    → ≤3 endpoints AND no sensitive subdomains (admin, dev, internal)
   - "medium" → 4-6 endpoints OR admin/dev subdomain present
   - "high"   → 7+ endpoints OR sensitive patterns found (/auth, /api, /internal, /admin)

3. SUMMARY:
   - Neutral and evidence-based
   - No speculation without supporting data
   - 1–2 sentences max

4. CITATIONS:
   - Must include the main domain URL
   - Must include any relevant subdomain URLs found

---

OUTPUT FORMAT (strict JSON, no markdown, no code blocks):

{{
  "domain": "string",
  "summary": "string",
  "risk_level": "low | medium | high",
  "subdomains": ["list of found subdomains"],
  "endpoints": ["list of found endpoints"],
  "technologies": ["list of detected technologies"],
  "insights": ["analytical observation 1", "analytical observation 2"],
  "citations": ["https://example.com", "https://sub.example.com"]
}}

RETURN ONLY THE JSON OBJECT. NO OTHER TEXT.
"""

    llm_output = generate_report(prompt, model)
    cleaned = clean_llm_output(llm_output)
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            parsed["subdomains"] = data["subdomains"]
            parsed["endpoints"] = data["endpoints"]
    except:
        parsed = {
        "domain": domain,
        "summary": cleaned,
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