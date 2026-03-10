from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    session_id: str
    query: str
    analysis_mode: str
    route: str
    in_scope: bool
    policy_message: str
    tasks: list[str]
    search_results: list[dict[str, Any]]
    documents: list[dict[str, str]]
    retrieved_context: list[dict[str, Any]]
    market_analysis: dict[str, Any]
    financial_analysis: dict[str, Any]
    risk_analysis: dict[str, Any]
    final_answer: str
    recommendation: str
    risk_level: str
    top_startup: str
    sources: list[str]
    evaluation: dict[str, float]
    trace_id: str
