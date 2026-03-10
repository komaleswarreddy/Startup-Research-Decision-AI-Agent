import os
from uuid import uuid4

import requests
import streamlit as st


st.set_page_config(page_title="Startup Research Agent", layout="wide")
st.title("Autonomous Startup Research & Decision AI Agent")
st.caption("Groq + LangGraph + Memory + Evaluation + Observability")

api_base_url = os.getenv("API_BASE_URL", "http://localhost:8000")

if "session_id" not in st.session_state:
    st.session_state.session_id = f"st-{uuid4().hex[:8]}"

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
