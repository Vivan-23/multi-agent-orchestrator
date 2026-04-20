# Step-by-Step Understanding of the Agent Pipeline

This document breaks down the LangGraph agent pipeline that runs when you submit a request.

## 1. User Input & Initialization
- The user provides a target domain/URL and selects an LLM model via the frontend UI.
- The FastAPI backend (`/run` endpoint) generates a unique `run_id` and initializes the `AgentState`.
- The pipeline starts executing the LangGraph defined in `src/Core/orchestrator.py`.

## 2. Recon Agent (`recon_agent`)
**Goal:** Gather raw intelligence about the target domain.
- **Target Formatting:** Ensures the input is a valid URL and extracts the base domain.
- **Technology Analysis:** Scans the domain to identify the tech stack (e.g., React, Nginx).
- **Subdomain Enumeration:** Discovers subdomains associated with the base domain.
- **Endpoint Scanning:** Probes for accessible endpoints on the main domain.
- **Data Storage:** Saves the raw HTML content, subdomains, endpoints, and domain info into the state's `data` dictionary.

## 3. Processing Agent (`processing_agent`)
**Goal:** Clean and structure the raw intelligence.
- **Deduplication:** Removes any duplicate subdomains and endpoints to prevent noise.
- **Filtering by Status:** Categorizes endpoints into `open` and `forbidden`.
- **Sensitive Path Detection:** Identifies notable forbidden endpoints (like `/admin`, `/auth`, `/.env`) that might be of interest for security auditing.
- **Data Storage:** Stores the filtered and structured endpoints back into the state.

## 4. Report Agent (`report_agent`)
**Goal:** Analyze the structured data and generate a security report using an LLM.
- **Prompt Construction:** Builds a strict prompt containing the domain info, deduplicated subdomains, filtered endpoints, and raw page content.
- **LLM Invocation:** Sends the prompt to the selected LLM model (e.g., Llama3 via Groq).
- **Rule Enforcement:** The LLM evaluates the risk level (low, medium, high) and generates analytical insights based on strict data integrity rules.
- **JSON Parsing:** The response is parsed into a structured JSON format containing the summary, risk level, insights, and citations.
- **Fallback Mechanism:** If the LLM output fails to parse, a fallback report is generated to ensure the pipeline completes successfully.

## 5. Evaluation & Storage
- After the pipeline finishes, the `evaluate` function calculates metrics like schema validity, unique sources, and tool error rates, assigning an evaluation score.
- The complete run state (including inputs, steps, data, and output report) is saved to `data/runs.json` and the logs are recorded.
- The frontend fetches the runs and displays the report, insights, and logs to the user.
