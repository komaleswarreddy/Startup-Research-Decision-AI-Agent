import json
import re

from app.agents.state import AgentState
from app.models.llm import LLMService


class DecisionAgent:
    def __init__(self, llm: LLMService) -> None:
        self.llm = llm

    def run(self, state: AgentState) -> AgentState:
        market = state.get("market_analysis", {})
        financial = state.get("financial_analysis", {})
        risk = state.get("risk_analysis", {})
        analysis_mode = state.get("analysis_mode", "single_decision")
        mode_instruction = (
            "This is a comparison request. Provide startup comparison insights and a shortlist rationale. "
            "Do not force a single buy recommendation if evidence is mixed."
            if analysis_mode == "comparison"
            else "This is a direct recommendation request. Provide a clear recommendation with rationale."
        )

        prompt = f"""
You are an AI startup investment analyst.
Use ONLY the provided analysis results. Do not invent facts.
{mode_instruction}

Query: {state.get("query", "")}
Market analysis: {market}
Financial analysis: {financial}
Risk analysis: {risk}
Sources: {state.get("sources", [])}

Return ONLY valid JSON with this schema:
{{
  "summary": "string",
  "key_market_insights": ["string"],
  "financial_outlook": "string",
  "risk_assessment": "string",
  "recommendation": "Buy | Hold | Avoid | Shortlist",
  "top_startup": "string",
  "confidence": 0.0
}}
"""
        raw = self.llm.summarize(prompt=prompt)
        payload = self._extract_json(raw)
        if payload:
            summary = str(payload.get("summary", "")).strip()
            insights = payload.get("key_market_insights", [])
            financial_outlook = str(payload.get("financial_outlook", "")).strip()
            risk_assessment = str(payload.get("risk_assessment", "")).strip()
            recommendation = str(payload.get("recommendation", "")).strip()
            top_startup = str(payload.get("top_startup", "")).strip()
            confidence = payload.get("confidence", 0.0)

            if not isinstance(insights, list):
                insights = []
            insights = [str(item) for item in insights if str(item).strip()][:5]

            if recommendation not in {"Buy", "Hold", "Avoid", "Shortlist"}:
                recommendation = "Hold"
            if not summary:
                summary = "Insufficient evidence for a complete recommendation."
            if not top_startup:
                top_startup = "Insufficient explicit startup signal"
            if not risk_assessment:
                risk_assessment = f"Risk level assessed as {state.get('risk_level', 'Medium-High')}."
            if not financial_outlook:
                financial_outlook = "Financial outlook is based on projected growth assumptions."

            state["final_answer"] = self._format_report(
                summary=summary,
                insights=insights,
                financial_outlook=financial_outlook,
                risk_assessment=risk_assessment,
                recommendation=recommendation,
                top_startup=top_startup,
                confidence=confidence,
            )
            state["recommendation"] = recommendation
            state["top_startup"] = top_startup
        else:
            state["final_answer"] = raw

        if not state.get("recommendation"):
            state["recommendation"] = "Hold"
        if not state.get("top_startup"):
            state["top_startup"] = "Insufficient explicit startup signal"
        if not state.get("risk_level"):
            state["risk_level"] = "Medium-High"
        return state

    @staticmethod
    def _extract_json(text: str) -> dict[str, object]:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            return {}
        try:
            parsed = json.loads(match.group(0))
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}

    @staticmethod
    def _format_report(
        summary: str,
        insights: list[str],
        financial_outlook: str,
        risk_assessment: str,
        recommendation: str,
        top_startup: str,
        confidence: object,
    ) -> str:
        insight_lines = "\n".join(f"- {item}" for item in insights) if insights else "- N/A"
        return (
            "Executive Summary:\n"
            f"{summary}\n\n"
            "Key Market Insights:\n"
            f"{insight_lines}\n\n"
            "Financial Outlook:\n"
            f"{financial_outlook}\n\n"
            "Risk Assessment:\n"
            f"{risk_assessment}\n\n"
            "Recommendation:\n"
            f"{recommendation}\n\n"
            "Top Startup:\n"
            f"{top_startup}\n\n"
            "Confidence:\n"
            f"{confidence}"
        )
