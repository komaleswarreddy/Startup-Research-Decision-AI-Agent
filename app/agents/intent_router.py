import json
import re
from dataclasses import dataclass

from app.models.llm import LLMService


@dataclass
class IntentResult:
    route: str
    in_scope: bool
    reason: str
    confidence: float = 0.0


class IntentRouter:
    STARTUP_KEYWORDS = {
        "startup",
        "startups",
        "investment",
        "invest",
        "investing",
        "funding",
        "valuation",
        "market",
        "tam",
        "sam",
        "som",
        "cagr",
        "unit economics",
        "revenue",
        "burn",
        "runway",
        "fintech",
        "ev",
        "saas",
        "healthtech",
        "edtech",
        "risk",
        "portfolio",
        "opportunity",
        "competitor",
        "competitive",
        "due diligence",
    }

    STARTUP_CREATION_CLUES = {
        "how to start",
        "start a startup",
        "startup in india",
        "startup idea in india",
        "startup idea",
        "business idea",
        "start startup in india",
        "how to start startup in india",
        "build a startup",
        "create a startup",
        "launch a startup",
        "set up a startup",
        "set up startup",
        "register company",
        "company registration",
        "incorporation",
        "dpiit",
        "legal requirements",
        "compliance",
        "founders agreement",
        "gst",
        "roc filing",
    }
    MARKET_ANALYSIS_CLUES = {
        "market size",
        "ecosystem",
        "industry",
        "industries",
        "trends",
        "government schemes",
        "policy support",
        "tax exemptions",
        "venture capital in india",
        "market research",
    }
    INVESTMENT_CLUES = {
        "invest",
        "investment",
        "funding",
        "valuation",
        "runway",
        "burn",
        "unit economics",
        "risk",
        "challenges",
        "opportunities",
        "recommend",
        "hold",
        "buy",
        "avoid",
    }
    COMPARISON_CLUES = {"compare", "comparison", "versus", "vs"}

    ALLOWED_INTENTS = {
        "startup_creation",
        "startup_investment",
        "market_analysis",
        "startup_comparison",
        "general_information",
        "out_of_scope",
    }

    def __init__(self, llm: LLMService | None = None) -> None:
        self.llm = llm or LLMService()

    def classify(self, query: str) -> IntentResult:
        normalized = " ".join(re.findall(r"[a-zA-Z0-9]+", query.lower()))
        if not normalized:
            return IntentResult(
                route="out_of_scope",
                in_scope=False,
                reason="Empty or invalid query.",
                confidence=1.0,
            )

        if any(clue in normalized for clue in self.STARTUP_CREATION_CLUES):
            return IntentResult(
                route="startup_creation",
                in_scope=True,
                reason="Query matches startup creation guidance workflow.",
                confidence=0.9,
            )

        if any(clue in normalized for clue in self.COMPARISON_CLUES):
            return IntentResult(
                route="startup_comparison",
                in_scope=True,
                reason="Query matches startup comparison workflow.",
                confidence=0.85,
            )

        if any(clue in normalized for clue in self.MARKET_ANALYSIS_CLUES):
            return IntentResult(
                route="market_analysis",
                in_scope=True,
                reason="Query matches market analysis workflow.",
                confidence=0.82,
            )

        if any(clue in normalized for clue in self.INVESTMENT_CLUES):
            return IntentResult(
                route="startup_investment",
                in_scope=True,
                reason="Query matches startup investment workflow.",
                confidence=0.82,
            )

        llm_result = self._classify_with_llm(query)
        if llm_result and llm_result.confidence >= 0.8:
            if llm_result.route == "general_information":
                return IntentResult(
                    route="out_of_scope",
                    in_scope=False,
                    reason=(
                        "This assistant is specialized for startup research and decision intelligence. "
                        "Please ask startup/investment-related questions."
                    ),
                    confidence=llm_result.confidence,
                )
            return llm_result

        match_count = sum(1 for keyword in self.STARTUP_KEYWORDS if keyword in normalized)
        if match_count >= 1:
            if any(clue in normalized for clue in self.COMPARISON_CLUES):
                return IntentResult(
                    route="startup_comparison",
                    in_scope=True,
                    reason="Query matches startup comparison workflow.",
                    confidence=0.68,
                )
            return IntentResult(
                route="startup_investment",
                in_scope=True,
                reason="Query matches startup investment analysis domain.",
                confidence=0.6,
            )

        return IntentResult(
            route="out_of_scope",
            in_scope=False,
            reason=(
                "This assistant is specialized for startup research and decision intelligence. "
                "Please ask startup/investment-related questions."
            ),
            confidence=0.6,
        )

    def _classify_with_llm(self, query: str) -> IntentResult | None:
        prompt = f"""
You are a query classification system.

Classify the user's query into one of these categories:
- startup_creation
- startup_investment
- market_analysis
- startup_comparison
- general_information
- out_of_scope

Return JSON only:
{{
  "intent": "startup_creation | startup_investment | market_analysis | startup_comparison | general_information | out_of_scope",
  "confidence": 0.0
}}

User query: {query}
"""
        raw = self.llm.summarize(prompt)
        match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
        if not match:
            return None
        try:
            payload = json.loads(match.group(0))
        except Exception:
            return None
        intent = str(payload.get("intent", "")).strip()
        confidence_raw = payload.get("confidence", 0.0)
        try:
            confidence = float(confidence_raw)
        except Exception:
            confidence = 0.0
        confidence = max(0.0, min(1.0, confidence))
        if intent not in self.ALLOWED_INTENTS:
            return None
        in_scope = intent != "out_of_scope"
        reason = (
            "Intent classified by LLM router."
            if in_scope
            else "This assistant is specialized for startup research and decision intelligence."
        )
        return IntentResult(route=intent, in_scope=in_scope, reason=reason, confidence=confidence)
