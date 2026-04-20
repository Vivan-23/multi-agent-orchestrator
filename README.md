# Agentic AI Recon Interface

A cybersecurity reconnaissance agent pipeline built with LangGraph and FastAPI. This interface automates the gathering of domain information, subdomains, and endpoints, and generates a security report using LLMs.

## Features

- **Automated Reconnaissance**: Automatically fetches domain technologies, subdomains, and endpoints.
- **Agentic Pipeline**: Uses a state graph (LangGraph) with Recon, Processing, and Report agents.
- **Deduplication & Filtering**: Automatically deduplicates findings and flags notable forbidden endpoints.
- **LLM-Powered Reports**: Analyzes the findings and produces actionable security insights with risk assessment.
- **FastAPI Backend & UI**: Provides an easy-to-use API and frontend.

## Getting Started

### Prerequisites

- Python 3.9+
- Docker & Docker Compose (optional, for containerized deployment)

### Setup

1. **Clone the repository:**
   ```bash
   git clone <repo_url>
   cd MyAgentProject
   ```

2. **Set up virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables:**
   Copy `.env-example` to `.env` and add your API keys.
   ```bash
   cp .env-example .env
   ```

5. **Run the application:**
   ```bash
   uvicorn src.main:app --reload
   ```
   Or using Docker:
   ```bash
   docker-compose up --build
   ```

6. **Access the Interface:**
   Open your browser and navigate to `http://localhost:8000`.
