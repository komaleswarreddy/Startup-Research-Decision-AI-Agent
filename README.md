# Autonomous Startup Research & Decision AI Agent

Production-focused multi-agent startup intelligence platform with:

- Groq + `llama-3.3-70b-versatile`
- LangGraph orchestration and memory
- Tool Execution Agent (Python analytics and charts)
- Evaluation Agent (faithfulness, grounding, confidence)
- Observability (LangSmith + OpenTelemetry + structured logs)
- Streamlit UI + FastAPI backend

## Quick start

1. Create and activate virtualenv.
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Copy `env.example` to `.env` and fill secrets.
4. Run API:
   - `uvicorn main:app --reload --port 8000`
5. Run UI:
   - `streamlit run ui/streamlit_app.py`

## Docker (local production-like run)

- Build and start both services:
  - `docker compose up --build -d`
- API: `http://127.0.0.1:8000/health`
- UI: `http://127.0.0.1:8501`

## CI/CD and AWS deployment

- CI tests: `.github/workflows/ci.yml`
- API CD to AWS App Runner: `.github/workflows/cd-api-apprunner.yml`
- UI CD to AWS App Runner: `.github/workflows/cd-ui-apprunner.yml`
- Full beginner guide: `DEPLOY_AWS_APP_RUNNER.md`

## Fast fallback deploy (Render API + Streamlit UI)

Use this when AWS is unavailable:

1. Deploy API on Render
   - Push repo to GitHub
   - In Render, create Blueprint from repo (uses `render.yaml`)
   - Set required env vars in Render:
     - `GROQ_API_KEY`
     - `TAVILY_API_KEY`
   - Wait for deploy, then verify:
     - `https://<your-render-service>.onrender.com/health`
     - `https://<your-render-service>.onrender.com/health/rag`

2. Deploy UI on Streamlit Community Cloud
   - New app from same GitHub repo
   - Main file path: `ui/streamlit_app.py`
   - In app settings -> Secrets, set:
     - `API_BASE_URL="https://<your-render-service>.onrender.com"`
   - Deploy and test with a startup query

3. Notes
   - First request can be slow due to cold start.
   - Keep `RAG_ENABLE_RERANKER=false` for faster startup on low-cost plans.

## 100% free deploy (Streamlit only, no AWS/Render)

The Streamlit app supports direct mode, so you can run agent workflows without a separate FastAPI host.

1. Push latest repo to GitHub.
2. Open Streamlit Community Cloud and create a new app.
3. Select:
   - Repository: this repo
   - Branch: `main`
   - Main file path: `ui/streamlit_app.py`
   - Python runtime: uses `runtime.txt` (`python-3.11`)
4. In Streamlit app settings -> Secrets, add:

```toml
GROQ_API_KEY="your_groq_key"
TAVILY_API_KEY="your_tavily_key"
STREAMLIT_DIRECT_MODE="true"
RAG_ENABLE_RERANKER="false"
LANGCHAIN_TRACING_V2="false"
```

5. Deploy app and run a test query from UI.

Notes:
- No separate backend URL is needed in direct mode.
- Free tiers can be slow on first request.
- If Streamlit asks for dependencies file path, set it to `ui/requirements.txt`.

## Main endpoint

- `POST /query`

Request:

```json
{
  "session_id": "optional",
  "query": "Analyze Indian EV startups and recommend top opportunities"
}
```

Response includes:

- analysis
- recommendation
- risk_level
- top_startup
- sources
- evaluation scores
- trace_id

## Reliability and memory options

You can tune reliability and persistence via env vars:

- `LLM_MAX_RETRIES`, `LLM_RETRY_BASE_SECONDS`
- `TOOL_MAX_RETRIES`, `TOOL_RETRY_BASE_SECONDS`
- `TOOL_CIRCUIT_BREAKER_FAILURES`, `TOOL_CIRCUIT_BREAKER_SECONDS`
- `MEMORY_BACKEND` (`inmemory` or `sqlite`) with `MEMORY_DB_PATH`
- `CHECKPOINT_BACKEND` (`memory` or `sqlite`) with `CHECKPOINT_DB_PATH`