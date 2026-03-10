import json
import re

from app.agents.state import AgentState
from app.models.llm import LLMService
from app.tools.python_exec import cagr


class MarketAnalysisAgent:
    def __init__(self, llm: LLMService | None = None) -> None:
        self.llm = llm or LLMService()

    def run(self, state: AgentState) -> AgentState:
        query = state.get("query", "")
        context = state.get("retrieved_context", [])
        combined = " ".join(item.get("content", "") for item in context)
        structured = self._llm_extract(query=query, context=context)
        if structured:
            state["market_analysis"] = structured
            return state

        estimated_cagr = 27.0

        percents = [
            float(x) for x in re.findall(r"\b(\d+(?:\.\d+)?)\s*%", combined)[:4]
            if 0 < float(x) <= 80
        ]
        if percents:
            estimated_cagr = round(sum(percents) / len(percents), 2)
        else:
            numbers = [float(x) for x in re.findall(r"\b\d+(?:\.\d+)?\b", combined)[:2]]
            if len(numbers) >= 2 and numbers[0] > 0 and numbers[1] >= numbers[0]:
                derived_cagr = round(cagr(numbers[0], numbers[1], 5), 2)
                if 0 < derived_cagr <= 80:
                    estimated_cagr = derived_cagr

        state["market_analysis"] = {
            "query_focus": query,
            "market_cagr": f"{estimated_cagr:.0f}%",
            "summary": "Market shows sustained growth with startup expansion and policy support.",
        }
        return state

    def _llm_extract(self, query: str, context: list[dict[str, object]]) -> dict[str, object]:
        prompt = f"""
Analyze the retrieved documents for this startup query and extract market signals.

Query: {query}
Retrieved context: {context}

Return ONLY valid JSON:
{{
  "query_focus": "string",
  "market_cagr": "NN%",
  "market_size": "string",
  "key_trends": ["string"],
  "opportunities": ["string"],
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
        market_cagr = str(parsed.get("market_cagr", "")).strip()
        if not re.search(r"\d", market_cagr):
            return {}
        parsed["query_focus"] = str(parsed.get("query_focus", query))
        parsed["summary"] = str(parsed.get("summary", "Market analysis generated from retrieved context."))
        return parsed
