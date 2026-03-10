# Software Requirements Specification (SRS)
# Autonomous Startup Research & Decision AI Agent

## 1. Overview

### 1.1 Objective
Build a production-ready AI system that can research startup ecosystems, analyze market and financial signals, and generate structured investment recommendations.

### 1.2 Core User Outcome
Given a query like:

```text
Analyze Indian EV startups and recommend top investment opportunities.
```

the platform returns:

- market analysis
- startup ranking
- risk assessment
- investment recommendation
- confidence and quality metrics
- sources and tool traces

## 2. Scope and Key Decisions

### 2.1 Mandatory Technology Choices
- **LLM Provider**: Groq
- **Primary Model**: `llama-3.3-70b-versatile`
- **UI**: Streamlit
- **Agent Orchestration**: LangGraph
- **Backend API**: FastAPI
- **RAG Store**: ChromaDB

### 2.2 System Style
Stateful multi-agent architecture with tool execution, memory, evaluation, and observability.

## 3. Functional Requirements

### 3.1 Query Intake
- User submits research requests from Streamlit UI.
- Backend validates request and creates a `session_id`.

### 3.2 Planning and Decomposition
- Planner agent breaks user query into executable tasks:
  1. market research
  2. startup extraction
  3. financial analysis
  4. risk scoring
  5. recommendation synthesis

### 3.3 Web + Retrieval Research (RAG)
- Search and scraping tools gather external information.
- Retrieved documents are embedded and stored in vector DB.
- Similarity retrieval injects context into the model prompt.

### 3.4 Multi-Agent Analysis
Required agents:
- Coordinator Agent
- Planner Agent
- Research Agent
- Market Analysis Agent
- Financial Analysis Agent
- Risk Analysis Agent
- Decision Agent

### 3.5 Tool Execution Agent (New Powerful Feature)
Add a dedicated **Tool Execution Agent** capable of controlled Python execution for quant workflows.

#### Tool Execution Capabilities
- calculate market growth (CAGR, TAM growth, segment growth)
- create charts (trend lines, comparison bars, scenario charts)
- build financial projections (base/bull/bear)
- run ranking formulas and weighted scorecards

#### Example Output Format
```json
{
  "market_cagr": "27%",
  "top_startup": "Ather Energy",
  "risk_level": "Medium",
  "investment_recommendation": "Buy"
}
```

### 3.6 Final Decision Generation
System must return:
- executive summary
- startup-wise analysis
- risk and opportunity table
- recommendation with rationale
- confidence score
- citations/sources

## 4. Memory System (Mandatory)

### 4.1 Short-Term Memory
- Conversation state retained for the active session.
- Enables follow-up continuity:
  - User: "Analyze EV startups."
  - User: "Now compare with US EV startups."
  - Agent must reuse previous context and avoid restarting analysis.

### 4.2 Long-Term Memory (LangGraph Memory)
- Use **LangGraph memory/checkpointing** for persistent multi-turn reasoning.
- Persist:
  - user preferences
  - prior analyses
  - important extracted entities
  - intermediate agent decisions

### 4.3 Optional Infra Extension
- Redis can be added as a backing store for durable memory and scaling, but the default design must prioritize LangGraph memory architecture.

## 5. Evaluation Pipeline (Mandatory)

Add an **Evaluation Agent** that runs after each response.

### 5.1 Required Evaluation Functions
- hallucination detection
- retrieval quality scoring
- answer confidence scoring
- source grounding checks

### 5.2 Required Metrics
- context relevance
- answer faithfulness
- source grounding
- retrieval hit quality
- overall confidence score

### 5.3 Output Contract
Every final response must include machine-readable evaluation metadata.

Example:
```json
{
  "evaluation": {
    "context_relevance": 0.89,
    "answer_faithfulness": 0.92,
    "source_grounding": 0.90,
    "retrieval_score": 0.87,
    "confidence_score": 0.88
  }
}
```

## 6. Observability (Mandatory)

Production runtime must include full observability.

### 6.1 Required Tooling
- LangSmith (agent traces and run inspection)
- OpenTelemetry (distributed tracing + metrics)
- structured logging (JSON logs with correlation IDs)

### 6.2 What Must Be Observable
- agent node transitions in LangGraph
- tool calls (input/output/errors/latency)
- LLM request/response metadata
- retrieval latency and top-k quality
- evaluation scores per response

## 7. Non-Functional Requirements

### 7.1 Performance
- Typical response target: 5 to 15 seconds.
- Tool-heavy workflows may exceed this but should stream progress.

### 7.2 Scalability
- Support 100+ concurrent requests.
- Stateless API pods with externalized memory/checkpoints.

### 7.3 Reliability
- retries with exponential backoff
- circuit breaker for failing tools
- fallback prompts/model-routing policy

### 7.4 Security
- secure secrets management for API keys
- scoped tool permissions for Python execution
- input sanitization and output redaction for sensitive data

## 8. System Architecture

```text
User
  ->
Streamlit UI
  ->
FastAPI Backend
  ->
LangGraph Orchestrator
  |- Coordinator/Planner/Research/Analysis/Decision Agents
  |- Tool Execution Agent (Python)
  |- Evaluation Agent
  |- Memory Layer (LangGraph Checkpointer)
  ->
Tools
  |- Tavily Search
  |- Web Scraper
  |- Chroma Vector DB
  |- Python Compute + Charting
  ->
LLM (Groq: llama-3.3-70b-versatile)
  ->
Final Report + Metrics + Trace IDs
```

## 9. API Requirements

### 9.1 Primary Endpoint
`POST /query`

Request:
```json
{
  "session_id": "optional-or-generated",
  "query": "Analyze Indian EV startups and recommend top opportunities"
}
```

Response:
```json
{
  "analysis": "...",
  "recommendation": "Buy",
  "risk_level": "Medium",
  "top_startup": "Ather Energy",
  "sources": ["..."],
  "evaluation": {
    "context_relevance": 0.89,
    "answer_faithfulness": 0.92,
    "source_grounding": 0.90,
    "retrieval_score": 0.87,
    "confidence_score": 0.88
  },
  "trace_id": "otel-trace-id"
}
```

## 10. Project Structure

```text
ai-startup-agent/
├── app/
│   ├── api/
│   │   └── routes.py
│   ├── agents/
│   │   ├── coordinator.py
│   │   ├── planner.py
│   │   ├── researcher.py
│   │   ├── market_analyzer.py
│   │   ├── financial_analyzer.py
│   │   ├── risk_analyzer.py
│   │   ├── tool_executor.py
│   │   ├── evaluator.py
│   │   └── decision.py
│   ├── memory/
│   │   ├── short_term.py
│   │   ├── langgraph_checkpoint.py
│   │   └── long_term_store.py
│   ├── rag/
│   │   ├── vector_store.py
│   │   └── retriever.py
│   ├── tools/
│   │   ├── search_tool.py
│   │   ├── scraper.py
│   │   ├── python_exec.py
│   │   └── charting.py
│   ├── observability/
│   │   ├── logging.py
│   │   ├── tracing.py
│   │   └── metrics.py
│   └── config/
│       └── settings.py
├── ui/
│   └── streamlit_app.py
├── tests/
├── Dockerfile
├── requirements.txt
├── .env
└── main.py
```

## 11. requirements.txt (Updated)

```txt
fastapi==0.111.0
uvicorn==0.30.0
pydantic==2.8.0
python-dotenv==1.0.1

langchain==1.0.3
langgraph==0.2.16
langchain-core==0.3.20
langchain-community==0.3.0
langchain-groq==1.1.2

chromadb==0.5.4
sentence-transformers==3.0.0
tavily-python==0.3.2

streamlit==1.35.0

pandas==2.2.2
numpy==1.26.4
matplotlib==3.9.0

langsmith==0.1.99
opentelemetry-api==1.25.0
opentelemetry-sdk==1.25.0
opentelemetry-exporter-otlp==1.25.0
```

## 12. Deployment and Operations

### 12.1 Runtime
- Containerized deployment using Docker.
- FastAPI for backend service.
- Streamlit for UI service.

### 12.2 CI/CD
Pipeline stages:
1. lint + unit tests
2. integration tests for agent graph
3. evaluation regression checks
4. docker build and push
5. deployment to AWS

### 12.3 AWS Recommendation
```text
User -> Load Balancer -> FastAPI Service -> LangGraph Agents -> Tools/Vector DB
                             |
                             -> Streamlit UI Service
```

## 13. Acceptance Criteria

The system is accepted when:
- Groq with `llama-3.3-70b-versatile` is integrated and used in production flow.
- Streamlit UI can run full query-to-report flow.
- Tool Execution Agent can run Python analytics and generate chart artifacts.
- LangGraph memory supports multi-turn context continuity.
- Evaluation Agent returns required quality metrics per answer.
- LangSmith + OpenTelemetry + logs provide traceable agent decisions.

## 14. Final Notes

This version upgrades the project from a basic agentic assistant to a production-grade decision intelligence platform by adding:
- executable analytics (tool execution agent)
- stateful reasoning (LangGraph memory)
- measurable quality (evaluation pipeline)
- debuggable operations (observability)

## 15. Detailed End-to-End Todo Plan (100% Coverage)

Execution policy: no phase is marked complete unless all checklist items and exit gates pass.

### Phase 0: Project Setup and Baseline
- [ ] Initialize project structure from Section 10.
- [ ] Create `.env.example` with all required keys (`GROQ_API_KEY`, `TAVILY_API_KEY`, `LANGSMITH_API_KEY`, OTLP endpoint).
- [ ] Configure Python 3.11 virtual environment.
- [ ] Install dependencies from `requirements.txt`.
- [ ] Add pre-commit checks (format, lint, tests).
- [ ] Add base README with startup commands.

Exit gate:
- [ ] Local app starts without errors (`FastAPI` + `Streamlit`).

### Phase 1: Core API and Orchestration
- [ ] Implement `POST /query` endpoint contract exactly as Section 9.
- [ ] Build LangGraph state schema (`session_id`, messages, retrieved docs, tool outputs, evaluation metadata).
- [ ] Implement coordinator flow from query intake to final response.
- [ ] Add structured error responses for validation and runtime failures.

Exit gate:
- [ ] End-to-end request returns valid JSON structure with placeholders for all required output fields.

### Phase 2: Groq + Llama-3.3-70B Integration
- [ ] Implement `app/models/llm.py` using Groq client.
- [ ] Set default model to `llama-3.3-70b-versatile`.
- [ ] Add retry, timeout, and rate-limit handling.
- [ ] Add model fallback policy (same provider, alternate model if needed).

Exit gate:
- [ ] Model responses are stable across 20 repeated test prompts with no crash.

### Phase 3: RAG Pipeline
- [ ] Implement Tavily search tool and scraper.
- [ ] Build document normalization and chunking pipeline.
- [ ] Implement embeddings and Chroma indexing.
- [ ] Implement retriever with top-k and score threshold.
- [ ] Attach source citations to final answer.

Exit gate:
- [ ] Retrieved context appears in response and includes citations for every major claim.

### Phase 4: Tool Execution Agent (Python Analytics)
- [ ] Implement secure Python execution sandbox (`app/tools/python_exec.py`).
- [ ] Implement market CAGR calculator utilities.
- [ ] Implement chart generation utilities (`matplotlib`) and file handling.
- [ ] Implement financial projection module (base/bull/bear).
- [ ] Wire Tool Execution Agent node into LangGraph.
- [ ] Validate standardized output keys:
  - `market_cagr`
  - `top_startup`
  - `risk_level`
  - `investment_recommendation`

Exit gate:
- [ ] Agent successfully runs analytics on sample EV dataset and returns expected JSON format.

### Phase 5: Memory System (LangGraph Memory First)
- [ ] Implement short-term conversation memory per `session_id`.
- [ ] Implement LangGraph checkpointer persistence.
- [ ] Persist prior analyses, user preferences, and key entities.
- [ ] Implement memory retrieval on follow-up queries.
- [ ] (Optional) Add Redis backend adapter for scale.

Exit gate:
- [ ] Follow-up query ("compare with US EV startups") reuses prior Indian EV analysis without redoing full pipeline.

### Phase 6: Evaluation Pipeline
- [ ] Implement Evaluation Agent as final post-processing node.
- [ ] Add hallucination detection heuristics/rules.
- [ ] Compute retrieval score from retriever metadata.
- [ ] Compute confidence score from evidence + consistency signals.
- [ ] Compute context relevance, faithfulness, and source grounding metrics.
- [ ] Inject evaluation object into API response.

Exit gate:
- [ ] Every response includes all required evaluation metrics with numeric values.

### Phase 7: Observability and Monitoring
- [ ] Enable LangSmith tracing for each graph run.
- [ ] Integrate OpenTelemetry tracing and metrics export.
- [ ] Add JSON structured logging with `trace_id` and `session_id`.
- [ ] Log tool latency, failures, and retries.
- [ ] Build operational dashboard panels (latency, error rate, confidence trends).

Exit gate:
- [ ] A single `trace_id` can reconstruct full agent decision path across nodes and tool calls.

### Phase 8: Streamlit UI Completion
- [ ] Build query input, run button, and progress state.
- [ ] Display analysis, recommendation, risk level, and top startup.
- [ ] Display citations and evaluation metrics panel.
- [ ] Add conversation history panel (memory visibility).
- [ ] Add chart/image rendering from tool execution outputs.

Exit gate:
- [ ] Non-technical user can run full research flow and inspect outputs from UI only.

### Phase 9: Testing for 100% Requirement Coverage
- [ ] Unit tests for agents, tools, memory, and evaluators.
- [ ] Integration tests for full LangGraph workflow.
- [ ] Regression tests for fixed benchmark prompts.
- [ ] Failure-mode tests (tool timeout, LLM error, empty retrieval).
- [ ] Security tests for Python execution constraints.
- [ ] Load test for 100+ concurrent requests.

Exit gate:
- [ ] All tests pass in CI with zero critical failures.

### Phase 10: Deployment and Production Readiness
- [ ] Build Docker images for API and UI.
- [ ] Configure CI/CD pipeline stages from Section 12.
- [ ] Deploy to AWS environment.
- [ ] Configure secrets and environment management.
- [ ] Configure autoscaling and health checks.
- [ ] Configure backup/retention for memory and logs.

Exit gate:
- [ ] Production endpoint is healthy, observable, and reproducible from clean deployment.

## 16. Definition of Done (Nothing Must Remain)

This project is only complete when all items below are true:
- [ ] Groq + `llama-3.3-70b-versatile` is active in runtime.
- [ ] Streamlit UI completes query-to-report flow.
- [ ] Tool Execution Agent runs Python analytics and charts.
- [ ] LangGraph memory works across follow-up conversations.
- [ ] Evaluation metrics are always returned.
- [ ] Observability stack (LangSmith + OpenTelemetry + logs) is live.
- [ ] End-to-end tests and load tests pass.
- [ ] CI/CD deploys successfully to target AWS environment.
- [ ] No unresolved P0/P1 defects remain.

## 17. Final Closing Statement

This SRS now represents a complete implementation blueprint, not just a concept note.  
If the team executes this plan phase by phase with the exit gates above, all mandatory capabilities will be delivered with full traceability, quality measurement, and production reliability, with no critical feature left incomplete.
