from uuid import uuid4
import re
from functools import lru_cache

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.agents.graph import AgentGraphService
from app.agents.intent_router import IntentResult, IntentRouter
from app.config.settings import get_settings
from app.observability.tracing import configure_tracing
from app.rag.retriever import EmbeddingService, RerankerService
from app.rag.vector_store import ChromaVectorStore


configure_tracing()
router = APIRouter()
graph_service = AgentGraphService()
intent_router = IntentRouter()


class QueryRequest(BaseModel):
    query: str = Field(min_length=3)
    session_id: str | None = None


class QueryResponse(BaseModel):
    route: str
    in_scope: bool
    policy_message: str
    analysis: str
    recommendation: str
    risk_level: str
    top_startup: str
    sources: list[str]
    evaluation: dict[str, float]
    trace_id: str
    intent_confidence: float = 0.0


@lru_cache(maxsize=1)
def _rag_health_snapshot() -> dict[str, str]:
    settings = get_settings()
    status: dict[str, str] = {
        "chroma": "unavailable",
        "embeddings": "unavailable",
        "reranker": "disabled" if not settings.rag_enable_reranker else "unavailable",
    }

    try:
        store = ChromaVectorStore()
        status["chroma"] = "ok" if store.supports_semantic() else "fallback"
    except Exception:
        status["chroma"] = "unavailable"

    try:
        embedder = EmbeddingService()
        status["embeddings"] = "ok" if embedder.enabled else "unavailable"
    except Exception:
        status["embeddings"] = "unavailable"

    try:
        reranker = RerankerService()
        if settings.rag_enable_reranker:
            status["reranker"] = "ok" if reranker.enabled else "unavailable"
    except Exception:
        if settings.rag_enable_reranker:
            status["reranker"] = "unavailable"

    return status


@router.get("/health/rag")
def rag_health() -> dict[str, str]:
    return _rag_health_snapshot()


def _force_startup_creation_when_applicable(query: str, intent: IntentResult) -> IntentResult:
    normalized = " ".join(re.findall(r"[a-zA-Z0-9]+", query.lower()))
    strong_creation_clues = (
        "how to start startup",
        "start startup in india",
        "startup in india",
        "startup idea in india",
        "startup idea",
        "company registration",
        "register company",
        "dpiit",
        "incorporation",
        "startup india provide",
        "startup india benefits",
        "mudra loan",
        "tax exemptions",
        "tax exemption",
    )
    if any(clue in normalized for clue in strong_creation_clues):
        return IntentResult(
            route="startup_creation",
            in_scope=True,
            reason="API safety override routed query to startup creation workflow.",
            confidence=max(intent.confidence, 0.9),
        )

    # Market sizing/comparative ecosystem questions should stay in market analysis,
    # even when phrasing contains comparative terms.
    market_sizing_clues = (
        "how big",
        "market size",
        "ecosystem compared",
        "ecosystem comparison",
    )
    if any(clue in normalized for clue in market_sizing_clues):
        return IntentResult(
            route="market_analysis",
            in_scope=True,
            reason="API safety override routed query to market analysis workflow.",
            confidence=max(intent.confidence, 0.9),
        )
    return intent


@router.post("/query", response_model=QueryResponse)
def query_agent(request: QueryRequest) -> QueryResponse:
    intent = _force_startup_creation_when_applicable(
        request.query, intent_router.classify(request.query)
    )
    if not intent.in_scope:
        return QueryResponse(
            route=intent.route,
            in_scope=False,
            policy_message=intent.reason,
            analysis=intent.reason,
            recommendation="N/A",
            risk_level="N/A",
            top_startup="N/A",
            sources=[],
            evaluation={
                "context_relevance": 0.0,
                "answer_faithfulness": 0.0,
                "source_grounding": 0.0,
                "retrieval_score": 0.0,
                "confidence_score": 0.0,
            },
            trace_id="",
            intent_confidence=intent.confidence,
        )

    if intent.confidence < 0.6:
        return QueryResponse(
            route=intent.route,
            in_scope=True,
            policy_message=(
                "Intent confidence is low. Please clarify whether you want startup creation guidance, "
                "investment analysis, market analysis, or startup comparison."
            ),
            analysis=(
                "I need a bit more clarity to run the right workflow. "
                "Please specify one of: startup creation, investment analysis, market analysis, startup comparison."
            ),
            recommendation="N/A",
            risk_level="N/A",
            top_startup="N/A",
            sources=[],
            evaluation={
                "context_relevance": 0.0,
                "answer_faithfulness": 0.0,
                "source_grounding": 0.0,
                "retrieval_score": 0.0,
                "confidence_score": round(intent.confidence, 2),
            },
            trace_id="",
            intent_confidence=intent.confidence,
        )

    session_id = request.session_id or f"session-{uuid4().hex[:8]}"
    try:
        result = graph_service.run(
            session_id=session_id,
            query=request.query,
            route=intent.route,
            in_scope=intent.in_scope,
            policy_message=intent.reason,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "query_processing_failed",
                "message": f"Unable to process query: {exc}",
                "trace_id": "",
            },
        ) from exc

    return QueryResponse(
        route=intent.route,
        in_scope=True,
        policy_message=intent.reason,
        analysis=result.get("final_answer", ""),
        recommendation=result.get("recommendation", "Hold"),
        risk_level=result.get("risk_level", "Medium"),
        top_startup=result.get("top_startup", "Unknown"),
        sources=result.get("sources", []),
        evaluation=result.get("evaluation", {}),
        trace_id=result.get("trace_id", ""),
        intent_confidence=intent.confidence,
    )
