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
3. Copy `.env.example` to `.env` and fill secrets.
4. Run API:
   - `uvicorn main:app --reload --port 8000`
5. Run UI:
   - `streamlit run ui/streamlit_app.py`

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