import json
import re

from app.agents.state import AgentState
from app.models.llm import LLMService


class StartupCreationAgent:
    def __init__(self, llm: LLMService) -> None:
        self.llm = llm

    def run(self, state: AgentState) -> AgentState:
        prompt = f"""
You are an expert startup advisor for India.
Use only the provided context and produce a practical startup creation guide.
Avoid motivational language. Focus on legal steps, registration, funding, compliance, and execution.

Query: {state.get("query", "")}
Retrieved context: {state.get("retrieved_context", [])}
Sources: {state.get("sources", [])}

Return ONLY valid JSON:
{{
  "summary": "procedural summary focused on implementation steps in India",
  "startup_steps": ["string"],
  "legal_registration": ["string"],
  "funding_options": ["string"],
  "common_mistakes": ["string"],
  "first_90_day_plan": ["string"],
  "recommended_resources": ["string (prefer Startup India, MCA, SIDBI, Startup School)"]
}}

Ensure startup_steps includes lifecycle stages:
- idea validation
- company incorporation
- PAN/TAN and GST (if applicable)
- DPIIT Startup India recognition
- MVP build and launch
- fundraising preparation
"""
        raw = self.llm.summarize(prompt)
        payload = self._extract_json(raw)
        if not payload:
            state["final_answer"] = raw
            state["recommendation"] = "N/A"
            state["risk_level"] = "N/A"
            state["top_startup"] = "N/A"
            return state

        summary = str(payload.get("summary", "")).strip() or "Startup creation guidance generated."
        steps = self._as_list(payload.get("startup_steps"))
        legal = self._as_list(payload.get("legal_registration"))
        funding = self._as_list(payload.get("funding_options"))
        mistakes = self._as_list(payload.get("common_mistakes"))
        first_90_day_plan = self._as_list(payload.get("first_90_day_plan"))
        resources = self._as_list(payload.get("recommended_resources"))
        steps = self._enforce_minimum_startup_steps(steps)
        legal = self._enforce_legal_compliance_basics(legal)
        resources = self._enforce_recommended_resources(resources)

        state["final_answer"] = self._format_output(
            summary,
            steps,
            legal,
            funding,
            mistakes,
            first_90_day_plan,
            resources,
        )
        state["recommendation"] = "N/A"
        state["risk_level"] = "N/A"
        state["top_startup"] = "N/A"
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
    def _as_list(value: object) -> list[str]:
        if not isinstance(value, list):
            return []
        return [str(item) for item in value if str(item).strip()][:8]

    @staticmethod
    def _format_output(
        summary: str,
        steps: list[str],
        legal: list[str],
        funding: list[str],
        mistakes: list[str],
        first_90_day_plan: list[str],
        resources: list[str],
    ) -> str:
        def render(title: str, items: list[str]) -> str:
            body = "\n".join(f"- {item}" for item in items) if items else "- N/A"
            return f"{title}:\n{body}"

        return (
            f"Executive Summary:\n{summary}\n\n"
            f"{render('Startup Steps', steps)}\n\n"
            f"{render('Legal Registration', legal)}\n\n"
            f"{render('Funding Options', funding)}\n\n"
            f"{render('Common Mistakes', mistakes)}\n\n"
            f"{render('First 90-Day Plan', first_90_day_plan)}\n\n"
            f"{render('Recommended Resources', resources)}"
        )

    @staticmethod
    def _enforce_minimum_startup_steps(steps: list[str]) -> list[str]:
        required = [
            "Validate the startup idea with customer interviews and problem-solution fit.",
            "Incorporate the company (Private Limited, LLP, or Partnership) via MCA.",
            "Obtain PAN/TAN and complete GST registration if applicable.",
            "Apply for DPIIT recognition through Startup India portal.",
            "Build and launch an MVP, then collect user feedback.",
            "Prepare fundraising materials (pitch deck, metrics, financial plan).",
        ]
        merged = list(steps)
        if len(merged) < 5:
            merged.extend(required)
        return list(dict.fromkeys(merged))[:10]

    @staticmethod
    def _enforce_legal_compliance_basics(legal: list[str]) -> list[str]:
        required = [
            "MCA incorporation documents and Certificate of Incorporation.",
            "PAN and TAN registration for the entity.",
            "GST registration where turnover/activity requires it.",
            "Founder agreement, ESOP policy, and IP assignment documentation.",
        ]
        merged = list(legal)
        if len(merged) < 3:
            merged.extend(required)
        return list(dict.fromkeys(merged))[:10]

    @staticmethod
    def _enforce_recommended_resources(resources: list[str]) -> list[str]:
        required = [
            "Startup India portal (DPIIT recognition and schemes)",
            "Ministry of Corporate Affairs (MCA) portal",
            "SIDBI startup funding programs",
            "Y Combinator Startup School",
        ]
        merged = list(resources)
        if len(merged) < 3:
            merged.extend(required)
        return list(dict.fromkeys(merged))[:10]
