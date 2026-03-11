import os
import re
import sys
from pathlib import Path
from uuid import uuid4

import requests
import streamlit as st

# Ensure repo root is importable when Streamlit runs from ui/ entrypoint.
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.agents.graph import AgentGraphService
from app.agents.intent_router import IntentResult, IntentRouter


st.set_page_config(page_title="Startup Research Agent", layout="wide")
st.title("Autonomous Startup Research & Decision AI Agent")
st.caption("Groq + LangGraph + Memory + Evaluation + Observability")

api_base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
direct_mode = os.getenv("STREAMLIT_DIRECT_MODE", "false").lower() == "true"

if "session_id" not in st.session_state:
    st.session_state.session_id = f"st-{uuid4().hex[:8]}"


@st.cache_resource
def _get_direct_services() -> tuple[AgentGraphService, IntentRouter]:
    return AgentGraphService(), IntentRouter()


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
            reason="UI safety override routed query to startup creation workflow.",
            confidence=max(intent.confidence, 0.9),
        )
    return intent


def _run_query_direct(query: str, session_id: str) -> dict:
    graph_service, intent_router = _get_direct_services()
    intent = _force_startup_creation_when_applicable(query, intent_router.classify(query))
    if not intent.in_scope:
        return {
            "route": intent.route,
            "in_scope": False,
            "policy_message": intent.reason,
            "analysis": intent.reason,
            "recommendation": "N/A",
            "risk_level": "N/A",
            "top_startup": "N/A",
            "sources": [],
            "evaluation": {
                "context_relevance": 0.0,
                "answer_faithfulness": 0.0,
                "source_grounding": 0.0,
                "retrieval_score": 0.0,
                "confidence_score": 0.0,
            },
            "trace_id": "",
        }

    result = graph_service.run(
        session_id=session_id,
        query=query,
        route=intent.route,
        in_scope=intent.in_scope,
        policy_message=intent.reason,
    )
    return {
        "route": intent.route,
        "in_scope": True,
        "policy_message": intent.reason,
        "analysis": result.get("final_answer", ""),
        "recommendation": result.get("recommendation", "Hold"),
        "risk_level": result.get("risk_level", "Medium"),
        "top_startup": result.get("top_startup", "Unknown"),
        "sources": result.get("sources", []),
        "evaluation": result.get("evaluation", {}),
        "trace_id": result.get("trace_id", ""),
    }

query = st.text_area(
    "Research Query",
    placeholder="Analyze Indian EV startups and recommend top investment opportunities.",
)

if st.button("Run Analysis", type="primary"):
    if not query.strip():
        st.warning("Please enter a query.")
    else:
        with st.spinner("Running multi-agent workflow..."):
            try:
                if direct_mode:
                    data = _run_query_direct(query=query, session_id=st.session_state.session_id)
                else:
                    response = requests.post(
                        f"{api_base_url}/query",
                        json={"query": query, "session_id": st.session_state.session_id},
                        timeout=300,
                    )
                    response.raise_for_status()
                    data = response.json()

                if "route" not in data or "in_scope" not in data or "policy_message" not in data:
                    st.error(
                        "Backend response is from an older version. Restart backend to use "
                        "domain-constrained routing."
                    )
                    st.stop()

                if not data.get("in_scope", True):
                    st.warning(data.get("policy_message", "Query is out of scope."))
                    st.subheader("Out-of-Scope Response")
                    st.write(data.get("analysis", ""))
                    st.info(
                        "Try startup-focused prompts like:\n"
                        "- Analyze Indian EV startups and rank top opportunities.\n"
                        "- Compare fintech startup opportunities in India vs SEA.\n"
                        "- Build a risk-adjusted startup investment recommendation."
                    )
                    st.caption(
                        f"Route: {data.get('route', 'unknown')} | "
                        f"In scope: {data.get('in_scope', False)}"
                    )
                    st.caption(f"Trace ID: {data.get('trace_id', 'n/a')}")
                    st.stop()

                st.subheader("Decision Report")
                st.write(data.get("analysis", ""))

                if data.get("route") != "startup_creation":
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Recommendation", data.get("recommendation", "N/A"))
                    col2.metric("Top Startup", data.get("top_startup", "N/A"))
                    col3.metric("Risk Level", data.get("risk_level", "N/A"))

                st.subheader("Evaluation Metrics")
                st.json(data.get("evaluation", {}))

                st.subheader("Sources")
                for source in data.get("sources", []):
                    st.write(f"- {source}")

                st.caption(f"Route: {data.get('route', 'unknown')} | In scope: {data.get('in_scope', False)}")
                st.caption(f"Trace ID: {data.get('trace_id', 'n/a')}")
            except Exception as exc:
                st.error(f"Request failed: {exc}")
