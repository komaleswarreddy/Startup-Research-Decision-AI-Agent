import json
import re

from app.agents.state import AgentState
from app.models.llm import LLMService


class PlannerAgent:
    ALLOWED_TASKS = {
        "startup_creation_analysis",
        "market_analysis",
        "competitor_analysis",
        "investment_analysis",
        "financial_analysis",
        "risk_analysis",
        "regulatory_analysis",
        "startup_extraction",
        "final_recommendation",
        "geography_comparison",
    }

    def __init__(self, llm: LLMService | None = None) -> None:
        self.llm = llm or LLMService()

    def run(self, state: AgentState) -> AgentState:
        preserved = state.get("tasks", [])
        query = state.get("query", "").lower()
        route = state.get("route", "startup_investment")
        plan = self._plan_with_llm(query=query, route=route)
        if not plan:
            plan = self._fallback_plan(query, route)

        state["analysis_mode"] = str(plan.get("analysis_mode", "single_decision"))
        planned_tasks = [
            task for task in plan.get("tasks", [])
            if isinstance(task, str) and task in self.ALLOWED_TASKS
        ]
        if not planned_tasks:
            planned_tasks = self._fallback_plan(query, route)["tasks"]

        state["tasks"] = list(dict.fromkeys([*preserved, *planned_tasks]))
        return state

    def _plan_with_llm(self, query: str, route: str) -> dict[str, object]:
        prompt = f"""
You are an AI planning agent.

Your job is to determine which analysis steps are required for this user query.

Allowed tasks:
- startup_creation_analysis
- market_analysis
- competitor_analysis
- investment_analysis
- financial_analysis
- risk_analysis
- regulatory_analysis
- startup_extraction
- final_recommendation
- geography_comparison

Return ONLY valid JSON with this schema:
{{
  "analysis_mode": "single_decision" | "comparison",
  "tasks": ["allowed_task_1", "allowed_task_2"]
}}

Detected intent route: {route}
User query: {query}
"""
        raw = self.llm.summarize(prompt)
        payload = self._extract_json(raw)
        if not payload:
            return {}
        mode = payload.get("analysis_mode", "single_decision")
        tasks = payload.get("tasks", [])
        if not isinstance(mode, str) or not isinstance(tasks, list):
            return {}
        return {"analysis_mode": mode, "tasks": tasks}

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
    def _fallback_plan(query: str, route: str) -> dict[str, object]:
        if route == "startup_creation":
            return {
                "analysis_mode": "single_decision",
                "tasks": [
                    "startup_creation_analysis",
                    "regulatory_analysis",
                    "financial_analysis",
                    "risk_analysis",
                    "final_recommendation",
                ],
            }

        mode = "comparison" if "compare" in query or route == "startup_comparison" else "single_decision"
        tasks = [
            "startup_creation_analysis",
            "market_analysis",
            "startup_extraction",
            "financial_analysis",
            "risk_analysis",
            "regulatory_analysis",
            "final_recommendation",
        ]
        if mode == "comparison":
            tasks.insert(1, "geography_comparison")
            tasks.insert(2, "competitor_analysis")
        else:
            tasks.insert(2, "investment_analysis")
        return {"analysis_mode": mode, "tasks": tasks}
