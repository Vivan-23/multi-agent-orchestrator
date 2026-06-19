# Agentic AI Recon Interface

A cybersecurity reconnaissance agent pipeline built with LangGraph, FastAPI, and PostgreSQL. This interface automates the gathering of domain information, subdomains, and endpoints, and generates a security report using LLMs.

## Features

- **Automated Reconnaissance**: Automatically fetches domain info, subdomains, and open/forbidden endpoints using live integrations.
- **Threat Intelligence APIs**: Integrated with **VirusTotal** (domain reputation and subdomain lookup) and **Shodan** (IP service scans, ports, and vulnerabilities).
- **Agentic Pipeline**: Built with a state graph (LangGraph) consisting of Recon, Processing, and Report agents.
- **Robust State Management**: Powered by Pydantic (`AgentState`) with custom backward-compatibility for dictionary-like bracket operations.
- **Database Persistence**: Integrated with a PostgreSQL database via SQLAlchemy, recording all scan runs and step-by-step logs.
- **Sleek UI**: Displays real-time metrics, summaries, technologies, and collapsible subdomains (showing 7 items with a "Show More" dropdown for large lists).
- **Comprehensive Unit Tests**: Test suite verifying domain extraction and state subscriptability.

## Getting Started

### Prerequisites

- Python 3.9+
- Docker & Docker Compose
- VirusTotal & Shodan API keys (Free tier accounts work)

### Setup

1. **Clone the repository:**
   ```bash
   git clone <repo_url>
   cd MyAgentProject
   ```

2. **Environment Variables:**
   Copy `.env.example` to `.env` and fill in your details:
   ```bash
   cp .env.example .env
   ```
   Add your `VIRUSTOTAL_API_KEY` and `SHODAN_API_KEY`.

3. **Run the application (Docker Compose):**
   The simplest way to run the backend, frontend, and PostgreSQL database together:
   ```bash
   docker-compose up --build
   ```

4. **Access the Interface:**
   Open your browser and navigate to `http://localhost:8000`.

### Running Tests

You can run the unit test suite on the host using the local virtual environment:
```bash
.\venv\Scripts\activate
python -m unittest discover -s tests -p "test_*.py"
```

Or run the tests directly inside the running backend container:
```bash
docker exec myagentproject-backend-1 python -m unittest discover -s tests -p "test_*.py"
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. Copyright © 2026 Vivan Manish Shah. All Rights Reserved.
