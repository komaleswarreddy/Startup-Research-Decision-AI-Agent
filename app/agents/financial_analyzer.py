import json
import re

from app.agents.state import AgentState
from app.models.llm import LLMService
from app.tools.python_exec import project_revenue


class FinancialAnalysisAgent:
    def __init__(self, llm: LLMService | None = None) -> None:
        self.llm = llm or LLMService()

    def run(self, state: AgentState) -> AgentState:
        query = state.get("query", "").lower()
        structured = self._llm_extract(state)
        if structured:
            state["financial_analysis"] = structured
            return state

        market_cagr_raw = str(state.get("market_analysis", {}).get("market_cagr", "27%"))
        match = re.search(r"\d+(?:\.\d+)?", market_cagr_raw)
        growth_rate = float(match.group(0)) if match else 27.0
        growth_rate = max(5.0, min(45.0, growth_rate))

        base_revenue = 100.0
        if "seed" in query:
            base_revenue = 40.0
        elif "series a" in query:
            base_revenue = 70.0

        values = project_revenue(base_revenue=base_revenue, growth_rate=growth_rate, years=3)
        state["financial_analysis"] = {
            "projection_model": "base_case",
            "assumed_growth_rate": growth_rate,
            "projected_revenue": values,
            "summary": "Projected revenue path indicates healthy compounding growth.",
        }
        return state

    def _llm_extract(self, state: AgentState) -> dict[str, object]:
        prompt = f"""
Generate a financial outlook from the available market and context signals.

Query: {state.get("query", "")}
Market analysis: {state.get("market_analysis", {})}
Retrieved context: {state.get("retrieved_context", [])}

Return ONLY valid JSON:
{{
  "projection_model": "string",
  "assumed_growth_rate": 0.0,
  "projected_revenue": [0.0, 0.0, 0.0],
  "summary": "string"
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
        growth = parsed.get("assumed_growth_rate")
        projected = parsed.get("projected_revenue")
        if not isinstance(growth, (int, float)) or not isinstance(projected, list) or not projected:
            return {}
        parsed["summary"] = str(parsed.get("summary", "Financial outlook generated from available evidence."))
        return parsed
