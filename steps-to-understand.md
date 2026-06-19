# Step-by-Step Understanding of the Agent Pipeline

This document breaks down the LangGraph agent pipeline that runs when you submit a domain scan request.

## 1. User Input & Initialization
- The user provides a target domain/URL and selects an LLM model via the frontend UI.
- The FastAPI backend (`/run` endpoint) generates a unique `run_id` and initializes the `AgentState`.
- `AgentState` is a Pydantic `BaseModel` that has custom support for subscriptability (`state["key"]`) and `.get()` for backward-compatibility.
- The pipeline starts executing the LangGraph defined in `src/Core/orchestrator.py`.

## 2. Recon Agent (`recon_agent`)
**Goal:** Gather raw intelligence about the target domain.
- **Target Formatting & Scope**: Standardizes the input domain/URL, extracts the base domain (handling double extensions), and locks the scope for security.
- **VirusTotal Scanner**: Queries the VirusTotal API to pull registrar info, categories, and last analysis statistics (harmless/malicious votes).
- **Shodan Scanner**: Resolves the target's IP address and queries the Shodan API to retrieve open ports, banners, ISP information, and CVE vulnerabilities.
- **Subdomain & Endpoint Enumeration**: Probes for accessible subdomains and common path endpoints.
- **State Update**: Stores findings in `state["data"]`.

## 3. Processing Agent (`processing_agent`)
**Goal:** Clean and structure the raw intelligence.
- **Deduplication**: Removes duplicate subdomains and endpoints.
- **Status Classification**: Splits scanned endpoints into `open` and `forbidden`.
- **Sensitive Path Detection**: Flags security-relevant forbidden endpoints (like `/admin`, `/auth`, `/.env`) as notable forbidden findings.
- **State Update**: Stores clean structured findings back in the state.

## 4. Report Agent (`report_agent`)
**Goal:** Analyze findings and generate a structured JSON security report using an LLM.
- **Prompt Construction**: Compiles the domain information, subdomains, open endpoints, and notable forbidden paths into a prompt.
- **LLM Invocation**: Invokes the selected LLM (via Groq/OpenAI).
- **Enforcing Output Schema**: Parses the LLM's response. On success, it ensures all gathered subdomains and endpoints are mapped back into the output object.
- **Fallback Recovery**: If parsing fails, it fills the fields with clean fallbacks to prevent pipeline failure.
- **State Update**: Stores the final report in `state["output"]`.

## 5. Evaluation & Database Storage
- **Evaluation**: The `evaluate` helper calculates a quality metric score based on schema validity, unique sources, and tool errors.
- **PostgreSQL Database Storage**:
  - The final run data (inputs, output report, metrics) is stored in the `scan_runs` table.
  - Granular stage updates (start, complete, error) are logged in the `scan_logs` table.
- **Frontend Rendering**: The frontend loads the run from the database and renders the results, showing the first 7 subdomains with a collapsed "Show More" dropdown for the remainder.
