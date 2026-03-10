import json
import re

from app.agents.state import AgentState
from app.models.llm import LLMService


class RiskAnalysisAgent:
    def __init__(self, llm: LLMService | None = None) -> None:
        self.llm = llm or LLMService()

    def run(self, state: AgentState) -> AgentState:
        query = state.get("query", "").lower()
        # Only use LLM risk extraction when we have evidence-rich context.
        if state.get("retrieved_context") and state.get("query"):
            structured = self._llm_extract(state)
            if structured:
                state["risk_analysis"] = structured
                state["risk_level"] = str(structured.get("risk_level", "Medium-High"))
                return state

        source_count = len(state.get("sources", []))
        if source_count >= 3:
            risk_level = "Medium"
        elif source_count == 2:
            risk_level = "Medium-High"
        else:
            risk_level = "High"

        high_risk_terms = {"high risk", "downside", "uncertain", "speculative", "volatile"}
        if any(term in query for term in high_risk_terms):
            risk_level = "High"

        state["risk_analysis"] = {
            "risk_level": risk_level,
            "drivers": ["execution risk", "policy risk", "capital intensity"],
        }
        state["risk_level"] = risk_level
        return state

    def _llm_extract(self, state: AgentState) -> dict[str, object]:
        prompt = f"""
Assess startup investment risk based on available evidence.

Query: {state.get("query", "")}
Market analysis: {state.get("market_analysis", {})}
Financial analysis: {state.get("financial_analysis", {})}
Sources: {state.get("sources", [])}
Retrieved context: {state.get("retrieved_context", [])}

Return ONLY valid JSON:
{{
  "risk_level": "Low | Medium | Medium-High | High",
  "risk_score": 0.0,
  "drivers": ["string"],
  "mitigations": ["string"]
}}
"""
        raw = self.llm.summarize(prompt)
        match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
        if not match:
            return {}
        try:
            parsed = json.loads(match.group(0))
        except Exception:
            return {}
        if not isinstance(parsed, dict):
            return {}
        risk_level = str(parsed.get("risk_level", "")).strip()
        if risk_level not in {"Low", "Medium", "Medium-High", "High"}:
            return {}
        drivers = parsed.get("drivers", [])
        if not isinstance(drivers, list):
            parsed["drivers"] = []
        return parsed
