from app.agents.state import AgentState
from app.tools.charting import create_projection_chart
from app.tools.python_exec import SafePythonExecutor


class ToolExecutionAgent:
    def __init__(self) -> None:
        self.executor = SafePythonExecutor()

    def run(self, state: AgentState) -> AgentState:
        query = state.get("query", "").lower()
        analysis_mode = str(state.get("analysis_mode", "single_decision"))
        risk_level = str(state.get("risk_level", "Medium"))
        market_cagr = self._extract_market_cagr(state)
        top_startup = self._infer_top_startup(query, state)
        recommendation = self._infer_recommendation(market_cagr, risk_level, analysis_mode)

        code = """
market_cagr = input_market_cagr
top_startup = input_top_startup
risk_level = input_risk_level
investment_recommendation = input_recommendation
"""
        result = self.executor.execute(
            code=code,
            context={
                "input_market_cagr": int(round(market_cagr)),
                "input_top_startup": top_startup,
                "input_risk_level": risk_level,
                "input_recommendation": recommendation,
            },
        )

        projected = state.get("financial_analysis", {}).get("projected_revenue", [120, 150, 190])
        labels = ["Year 1", "Year 2", "Year 3"]
        chart_path = create_projection_chart(labels=labels, values=[float(v) for v in projected])

        output = {
            "market_cagr": f"{result.output.get('market_cagr', 27)}%",
            "top_startup": result.output.get("top_startup", top_startup),
            "risk_level": result.output.get("risk_level", risk_level),
            "investment_recommendation": result.output.get(
                "investment_recommendation", recommendation
            ),
            "chart_path": chart_path,
            "python_success": result.success,
            "python_error": result.error,
        }
        state["tool_output"] = output
        state["top_startup"] = output["top_startup"]
        state["recommendation"] = output["investment_recommendation"]
        state["risk_level"] = output["risk_level"]
        return state

    @staticmethod
    def _extract_market_cagr(state: AgentState) -> float:
        raw = str(state.get("market_analysis", {}).get("market_cagr", "27%"))
        digits = "".join(ch for ch in raw if ch.isdigit() or ch == ".")
        try:
            return max(1.0, min(60.0, float(digits)))
        except Exception:
            return 27.0

    @staticmethod
    def _infer_top_startup(query: str, state: AgentState) -> str:
        combined_text = " ".join(
            [
                str(item.get("content", ""))
                for item in state.get("retrieved_context", [])
            ]
            + [str(item.get("content", "")) for item in state.get("documents", [])]
            + [str(item.get("title", "")) for item in state.get("search_results", [])]
        )
        known_fintech = [
            "Razorpay",
            "PhonePe",
            "Paytm",
            "CRED",
            "Groww",
            "BharatPe",
            "Pine Labs",
            "Zerodha",
            "PolicyBazaar",
        ]
        for name in known_fintech:
            if name.lower() in combined_text.lower():
                return name

        if "fintech" in query:
            return "Top fintech startup candidate"
        if "ev" in query or "electric vehicle" in query:
            return "Top EV startup candidate"
        if "saas" in query:
            return "Top SaaS startup candidate"
        return "Top startup candidate"

    @staticmethod
    def _infer_recommendation(market_cagr: float, risk_level: str, analysis_mode: str) -> str:
        if analysis_mode == "comparison":
            if risk_level == "High":
                return "Hold"
            return "Shortlist"
        if risk_level == "High":
            return "Hold"
        if market_cagr >= 20 and risk_level in {"Medium", "Medium-High"}:
            return "Buy"
        if market_cagr < 8:
            return "Avoid"
        return "Hold"
