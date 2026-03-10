from app.agents.coordinator import CoordinatorAgent
from app.agents.evaluator import EvaluationAgent
from app.agents.market_analyzer import MarketAnalysisAgent
from app.agents.planner import PlannerAgent
from app.agents.researcher import ResearchAgent
from app.agents.risk_analyzer import RiskAnalysisAgent
from app.agents.startup_creation import StartupCreationAgent
from app.memory.long_term_store import LongTermMemoryStore
from app.memory.short_term import ShortTermMemoryStore


class _FakeSearchTool:
    def search(self, query: str, max_results: int = 5) -> list[dict[str, str]]:
        return [
            {"title": "A", "url": "https://a.example", "content": "India EV market growth 120 200"},
            {"title": "B", "url": "https://b.example", "content": "Battery policy and charging infra"},
        ]


class _FakeScraper:
    def enrich_results(self, search_results: list[dict[str, str]]) -> list[dict[str, str]]:
        return [
            {"source": item["url"], "content": item["content"]}
            for item in search_results
        ]


class _FakeLLM:
    def summarize(self, prompt: str) -> str:
        return (
            '{"summary":"Practical guide","startup_steps":["Incorporate entity"],'
            '"legal_registration":["PAN"],"funding_options":["Angel"],'
            '"common_mistakes":["Skipping compliance"],"first_90_day_plan":["Validate problem"],'
            '"recommended_resources":["Startup India portal"]}'
        )


def test_planner_adds_compare_task() -> None:
    planner = PlannerAgent()
    state = planner.run({"query": "Compare India and US EV startup opportunities"})
    assert "geography_comparison" in state["tasks"]
    assert state["analysis_mode"] == "comparison"


def test_coordinator_merges_long_term_context_and_history_marker() -> None:
    short_term = ShortTermMemoryStore()
    long_term = LongTermMemoryStore()
    session_id = "s-1"
    short_term.add_message(session_id, "user", "First question")
    long_term.upsert(session_id, "last_analysis", "Prior decision summary")
    coordinator = CoordinatorAgent(short_term_memory=short_term, long_term_memory=long_term)

    state = coordinator.pre_run({"session_id": session_id, "query": "Follow up query", "tasks": []})

    assert state["retrieved_context"][0]["source"] == "long_term_memory"
    assert "follow_up_context_merge" in state["tasks"]


def test_market_analyzer_uses_extracted_numbers_for_cagr() -> None:
    agent = MarketAnalysisAgent()
    state = {
        "query": "Analyze market",
        "retrieved_context": [{"content": "market moved from 100 to 200"}],
    }
    result = agent.run(state)
    assert result["market_analysis"]["market_cagr"].endswith("%")
    assert result["market_analysis"]["market_cagr"] != "27%"


def test_market_analyzer_falls_back_when_no_numbers() -> None:
    agent = MarketAnalysisAgent()
    result = agent.run({"query": "Analyze market", "retrieved_context": [{"content": "no numerics"}]})
    assert result["market_analysis"]["market_cagr"] == "27%"


def test_risk_analyzer_thresholds() -> None:
    agent = RiskAnalysisAgent()
    assert agent.run({"sources": ["a", "b", "c"]})["risk_level"] == "Medium"
    assert agent.run({"sources": ["a", "b"]})["risk_level"] == "Medium-High"
    assert agent.run({"sources": ["a"]})["risk_level"] == "High"


def test_risk_analyzer_respects_high_risk_query_term() -> None:
    agent = RiskAnalysisAgent()
    out = agent.run({"sources": ["a", "b", "c"], "query": "seed investing with high downside risk"})
    assert out["risk_level"] == "High"


def test_evaluator_with_and_without_retrieval_context() -> None:
    evaluator = EvaluationAgent()
    no_ctx = evaluator.run({"sources": []})["evaluation"]
    assert no_ctx["retrieval_score"] == 0.4

    with_ctx = evaluator.run(
        {
            "retrieved_context": [{"score": 0.6}, {"score": 0.8}],
            "sources": ["a", "b", "c"],
        }
    )["evaluation"]
    assert with_ctx["retrieval_score"] == 0.7
    assert 0 <= with_ctx["confidence_score"] <= 1


def test_research_agent_populates_context_and_sources() -> None:
    agent = ResearchAgent(search_tool=_FakeSearchTool(), scraper=_FakeScraper())
    result = agent.run({"query": "India EV growth"})
    assert len(result["search_results"]) == 2
    assert len(result["documents"]) == 2
    assert len(result["retrieved_context"]) >= 1
    assert all("source" in item for item in result["retrieved_context"])


def test_startup_creation_agent_enforces_operational_sections() -> None:
    agent = StartupCreationAgent(llm=_FakeLLM())  # type: ignore[arg-type]
    out = agent.run({"query": "how to start startup in india"})
    text = out["final_answer"]
    assert "Startup Steps" in text
    assert "Legal Registration" in text
    assert "First 90-Day Plan" in text
    assert out["recommendation"] == "N/A"
