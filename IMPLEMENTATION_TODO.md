# Detailed Todo Plan - Full Implementation Coverage

This tracker is execution-first. Do not skip phases. A phase is complete only if every item and gate is complete.

## Phase 0 - Environment and Setup
- [x] Create project structure (`app`, `ui`, `tests`).
- [x] Add `requirements.txt`.
- [x] Add `.env.example` with all required keys.
- [x] Add startup docs in `README.md`.
- [ ] Create `.env` from `.env.example`.
- [ ] Install dependencies in virtual environment.

Gate:
- [ ] `uvicorn main:app --reload` starts successfully.
- [ ] `streamlit run ui/streamlit_app.py` starts successfully.

## Phase 1 - Core API and Models
- [x] Build FastAPI app in `main.py`.
- [x] Implement `/health`.
- [x] Implement `POST /query` endpoint contract.
- [x] Add request/response schema validation.
- [ ] Add API error envelope standardization.

Gate:
- [ ] `POST /query` returns all required keys under success and failure paths.

## Phase 2 - LangGraph Multi-Agent Workflow
- [x] Define `AgentState`.
- [x] Implement coordinator, planner, researcher, market, financial, risk, tool executor, decision, evaluator agents.
- [x] Build LangGraph state machine with sequential edges.
- [x] Enable LangGraph checkpointer for memory threads.
- [ ] Add conditional branching and retry edges.

Gate:
- [ ] Single graph run completes with no node failure.
- [ ] Follow-up run on same `session_id` uses prior thread.

## Phase 3 - Groq LLM Integration
- [x] Add LLM service abstraction.
- [x] Integrate Groq client with default model `llama-3.3-70b-versatile`.
- [x] Add fallback behavior when key is missing.
- [ ] Add provider/model fallback routing policy.
- [ ] Add token usage and cost logging.

Gate:
- [ ] Valid `.env` key triggers real Groq inference end-to-end.

## Phase 4 - RAG Pipeline
- [x] Implement Tavily search tool.
- [x] Implement scraping enrichment tool.
- [x] Implement in-memory vector store wrapper.
- [x] Implement lexical retriever with scoring.
- [ ] Upgrade to embedding + Chroma persisted index.
- [ ] Add chunking and deduplication.

Gate:
- [ ] Citations included for major report claims.
- [ ] Retrieval score updates per query.

## Phase 5 - Tool Execution Agent (Python)
- [x] Add safe Python executor.
- [x] Add CAGR and projection helpers.
- [x] Add chart generation utility.
- [x] Wire tool output into final response.
- [ ] Add stricter sandbox controls (timeouts/process isolation).
- [ ] Add file-size and runtime limits.

Gate:
- [ ] Returns:
  - `market_cagr`
  - `top_startup`
  - `risk_level`
  - `investment_recommendation`
- [ ] Chart image is created and renderable in UI.

## Phase 6 - Memory System
- [x] Add short-term session conversation memory.
- [x] Add long-term memory store abstraction.
- [x] Add LangGraph checkpoint memory.
- [x] Save final answer and recommendation for follow-up reuse.
- [ ] Add Redis-backed persistent memory adapter.
- [ ] Add memory pruning and retention policies.

Gate:
- [ ] Query 2 references Query 1 context on same `session_id`.

## Phase 7 - Evaluation Pipeline
- [x] Add evaluation agent node after decision.
- [x] Compute context relevance, faithfulness, source grounding.
- [x] Compute retrieval score and confidence score.
- [x] Attach `evaluation` object to API response.
- [ ] Add explicit hallucination classifier.
- [ ] Add benchmark evaluation dataset.

Gate:
- [ ] Every `/query` response contains complete evaluation metadata.

## Phase 8 - Observability
- [x] Add structured JSON logging.
- [x] Add OpenTelemetry bootstrap.
- [x] Include `trace_id` in response.
- [ ] Add LangSmith run metadata capture per node.
- [ ] Add dashboards/alerts (latency, error rate, confidence drift).

Gate:
- [ ] A response `trace_id` maps to logs + traces for the full run.

## Phase 9 - Streamlit UI
- [x] Build query input and run action.
- [x] Display report and decision summary.
- [x] Display evaluation metrics.
- [x] Display sources and tool output.
- [x] Render generated chart image if present.
- [ ] Add chat history pane and previous-run comparison view.

Gate:
- [ ] End user can complete full workflow from UI only.

## Phase 10 - Testing and CI/CD
- [x] Add API contract test skeleton.
- [x] Add health test.
- [ ] Add agent-level unit tests.
- [ ] Add integration tests for memory follow-up behavior.
- [ ] Add load tests for 100+ concurrent requests.
- [ ] Add CI pipeline with lint, tests, and build.

Gate:
- [ ] CI green on all required stages.

## Phase 11 - Deployment
- [ ] Add Dockerfile for API + UI services.
- [ ] Add deployment manifests/scripts.
- [ ] Configure secrets management and health checks.
- [ ] Configure production logging/tracing exporters.

Gate:
- [ ] Production deployment passes smoke tests and observability checks.

## Hard Definition of Done
- [ ] Groq + `llama-3.3-70b-versatile` active in production flow.
- [ ] Streamlit end-to-end flow works.
- [ ] Tool Execution Agent runs analytics + charts.
- [ ] LangGraph memory supports follow-up continuity.
- [ ] Evaluation metrics always present in output.
- [ ] Observability (logs + traces + LangSmith) fully active.
- [ ] Tests and CI/CD complete.
- [ ] No unresolved critical defects.
