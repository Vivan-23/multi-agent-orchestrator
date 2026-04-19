

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
import re
from src.Core.logger import log_event


# 🔍 RECON AGENT
def recon_agent(state):
    run_id = state.run_id

    try:
        log_event("recon", "start", "running", run_id)
        state.steps.append("Recon started")

        url = state.input
        if not url.startswith("http"):
            url = "https://" + url

        state.steps.append(f"Target formatted to {url}")
        domain = url.replace("https://", "").replace("http://", "").split("/")[0]

        state.steps.append(f"Extracted domain: {domain}")
        homepage = fetch_url(url)
        state.steps.append("Fetched homepage content")

        # 🔥 fallback check
        if not homepage or homepage.startswith("Error"):
            state.data = {
                "domain_info": {"domain": domain, "technologies": []},
                "subdomains": [],
                "endpoints": [],
                "raw_text": ""
            }
            state.steps.append("Recon fallback used")

            log_event("recon", "complete", "success", run_id)
            return state

        # normal flow
        state.steps.append("Analyzing domain technology")
        domain_info = analyze_domain(domain)
        state.steps.append("Extracting base domain")
        base_domain = extract_base_domain(url)
        state.steps.append("Searching and validating subdomains")
        subdomains = find_subdomains(base_domain)
        state.steps.append("Scanning and probing endpoints")
        endpoints = scan_endpoints(domain)

        state.data = {
            "domain_info": domain_info,
            "subdomains": subdomains,
            "endpoints": endpoints,
            "raw_text": homepage
        }

        state.steps.append("Recon completed")

        log_event("recon", "complete", "success", run_id)
        return state

    except Exception as e:
        log_event("recon", "failed", "error", run_id, str(e))
        state.errors += 1
        return state
    
    
# ⚙️ PROCESSING AGENT
# def processing_agent(state):
#     run_id = state["run_id"]

#     try:
#         log_event("processing", "start", "running", run_id)
#         state["steps"].append("Processing started")

#         data = state["data"]

#         state["steps"].append("Deduplicating subdomains")
#         data["subdomains"] = deduplicate(data["subdomains"])
#         state["steps"].append("Deduplicating endpoints")
#         data["endpoints"] = deduplicate(data["endpoints"])

#         state["data"] = data
#         state["steps"].append("Processing completed")

#         log_event("processing", "complete", "success", run_id)
#         return state

#     except Exception as e:
#         log_event("processing", "failed", "error", run_id, str(e))
#         state["errors"] += 1
#         return state

def filter_endpoints(endpoints):
    if not endpoints:
        return {"open": [], "forbidden_count": 0, "notable_forbidden": []}

    # handle old format (plain strings) vs new format (dicts with status)
    if isinstance(endpoints[0], str):
        return {"open": endpoints, "forbidden_count": 0, "notable_forbidden": []}

    sensitive_paths = [
        "/admin", "/auth", "/internal", "/api",
        "/.git", "/.env", "/config", "/secret",
        "/dashboard", "/graphql", "/swagger"
    ]

    open_ep = [e["url"] for e in endpoints if e["status"] == "open"]
    forbidden = [e for e in endpoints if e["status"] == "forbidden"]
    notable = [
        e["url"] for e in forbidden
        if any(path in e["url"] for path in sensitive_paths)
    ]

    return {
        "open": open_ep,
        "forbidden_count": len(forbidden),
        "notable_forbidden": notable
    }


def processing_agent(state):
    run_id = state.run_id

    try:
        log_event("processing", "start", "running", run_id)
        state.steps.append("Processing started")

        data = state.data

        # deduplicate
        state.steps.append("Deduplicating subdomains")
        data["subdomains"] = deduplicate(data["subdomains"])

        state.steps.append("Deduplicating endpoints")
        data["endpoints"] = deduplicate(data["endpoints"])

        # filter endpoints by status
        state.steps.append("Filtering endpoints by status")
        data["filtered_endpoints"] = filter_endpoints(data["endpoints"])

        state.data = data
        state.steps.append("Processing completed")

        log_event("processing", "complete", "success", run_id)
        return state

    except Exception as e:
        log_event("processing", "failed", "error", run_id, str(e))
        state.errors += 1
        return state

def parse_llm_response(response: str):
    try:
        # strip markdown code blocks
        cleaned = re.sub(r"```json|```", "", response).strip()
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # try extracting JSON object directly
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        return None

# 🧠 REPORT AGENT (no LLM yet)
def report_agent(state):
    run_id = state.run_id
    model = getattr(state, "model", "openai")
    
    log_event("report", "start", "running", run_id)
    state.steps.append("Report generation started")

    data = state.data
    filtered = data.get("filtered_endpoints", {
        "open": data["endpoints"],
        "forbidden_count": 0,
        "notable_forbidden": []
    })
    print("OPEN:", filtered["open"])
    print("FORBIDDEN:", filtered["forbidden_count"])
    domain = data["domain_info"]["domain"]

    state.steps.append(f"Constructing prompt for {domain}")

    prompt = f"""
You are a cybersecurity reconnaissance analyst. Analyze the recon data below and return a single JSON object.

═══════════════════════════════
RECON DATA (ground truth only)
═══════════════════════════════
Domain Info   : {data["domain_info"]}
Subdomains    : {data["subdomains"]}
Open Endpoints   : {filtered['open']}
Forbidden Endpoints : {filtered['forbidden_count']}
Notable Forbidden Endpoints : {filtered['notable_forbidden']}
Page Content  : {data["raw_text"][:500]}

═══════════════════════════════
STRICT RULES — follow in order
═══════════════════════════════
RULE 0 — CONTEXT AWARENESS
  Before assessing risk, determine the nature of the target:
  - If the domain is a well-known public platform (github.com, google.com, 
    twitter.com etc.), endpoints like /login, /signup, /dashboard are 
    INTENTIONAL and should NOT be flagged as vulnerabilities.
  - Only flag endpoints as risky if they are unexpected for that domain type.
  - /graphql on github.com = intentional public API, not a finding.
  - /phpmyadmin on github.com = unexpected, worth flagging.

RULE 1 — DATA INTEGRITY (highest priority)
  - ONLY use subdomains and endpoints that appear EXACTLY in the recon data above.
  - NEVER invent, infer, or guess subdomains or endpoints.
  - NEVER reference a subdomain or endpoint in insights unless it appears in the lists above.
  - If a list is empty, return an empty array for that field.

RULE 2 — INVALID DOMAIN
  Apply this rule ONLY IF all three are true:
    (a) Subdomains list is empty
    (b) Endpoints list is empty
    (c) Page Content is empty or an error message
  Then:
    - summary   → "The provided domain appears to be invalid or unreachable."
    - insights  → ["The provided domain is incorrect or unreachable. Please verify the target."]
    - risk_level → "low"
  Skip rules 3–5 entirely.

RULE 3 — RISK LEVEL
  Base risk ONLY on "Open Endpoints" and Subdomains.
  FOR PUBLIC PLATFORMS LIKE github.com,X.com,Youtube.com .... always low
  Forbidden endpoints are BLOCKED — do NOT count them as exposed.

  - "high"   → sensitive path (/auth, /internal, /admin) in Open Endpoints
               OR 6+ Open Endpoints
  - "medium" → admin/dev/staging SUBDOMAIN present
               OR 3–5 Open Endpoints
  - "low"    → ≤2 Open Endpoints and no sensitive subdomains
Never give High unless extremely sure about it .
RULE 4 — INSIGHTS (generate 3–5)
  Each insight MUST:
    - Be analytical, not descriptive (explain what it means, not what it is)
    - Reference a specific endpoint or subdomain from the data by name
    - Explain the security implication clearly
If data is sparse (no subdomains, no open endpoints), generate 
insights based on what WAS found — technologies, server headers, 
page content. Never return fewer than 2 insights.
[BANNED PHRASE]: Never use the phrase "publicly reachable without 
network restrictions" — it is forbidden. 
[CRITICAL]Each insight must be uniquely worded and specific to that 
finding. Do not reuse the same sentence structure across insights.
If technologies include a versioned server (e.g. Apache/2.4.7), 
check if the version is outdated and flag it as a finding.
  Quality bar:
    BAD  → "The site has a login page."
    BAD  → "nginx and React suggest a modern stack."
    GOOD → "The /login endpoint at docs.langchain.com is publicly reachable without
             network restrictions, making it a candidate for credential stuffing attacks."
    GOOD → "api.langchain.com exposed alongside /api/v1 suggests the API layer has
             no internal network boundary — enumeration or abuse is possible without
             additional rate limiting."
  
  If fewer than 3 unique analytical observations can be made from the data,
  state that explicitly in the insight rather than padding with weak observations.

RULE 5 — SUMMARY
  - 1–2 sentences only
  - Neutral and evidence-based — no words like "potentially" or "suggests" unless necessary
  - Must reference specific findings (e.g. number of endpoints, specific subdomains)
  - NO speculation beyond what the data supports

RULE 6 — CITATIONS
  - Always include the main domain URL
  - Include a URL for each subdomain found in the data
  - No invented URLs

═══════════════════════════════
OUTPUT FORMAT
═══════════════════════════════
Return ONLY this JSON object. No markdown. No code blocks. No explanation.

{{
  "domain": "string",
  "summary": "string",
  "risk_level": "low | medium | high",
  "subdomains": ["only from recon data"],
  "endpoints": ["only from recon data"],
  "technologies": ["only from recon data"],
  "insights": ["analytical observation 1", "...up to 5"],
  "citations": ["https://domain.com", "https://sub.domain.com"]
}}
""" 
    model_key = getattr(state, "model", "openai")
    state.steps.append(f"Invoking LLM with model: {model_key}")
    llm_output = generate_report(prompt, model_key)
    state.steps.append("Received LLM response")
    
    try:
        state.steps.append("Parsing LLM JSON output")
        parsed = parse_llm_response(llm_output)
        if not parsed:
            raise ValueError("Parse failed")
        state.steps.append("Successfully parsed JSON")
    except:
        state.steps.append("Failed to parse JSON, using fallback payload")
        parsed = {
            "domain": domain,
            "summary": "Failed to parse LLM output.",
            "subdomains": data["subdomains"] or [],
            "endpoints": data["endpoints"] or [],
            "technologies": data["domain_info"]["technologies"],
            "insights": ["Fallback due to parsing error"],
            "citations": [f"https://{domain}"]
        }
    print("MODEL:", model)
    print("CALLING LLM...")
    state.output = parsed
    state.steps.append("Report generation completed")
    
    log_event("report", "complete", "success", run_id)
    return state