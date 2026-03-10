from uuid import uuid4

from langgraph.graph import END, StateGraph

from app.agents.coordinator import CoordinatorAgent
from app.agents.decision import DecisionAgent
from app.agents.evaluator import EvaluationAgent
from app.agents.financial_analyzer import FinancialAnalysisAgent
from app.agents.market_analyzer import MarketAnalysisAgent
from app.agents.planner import PlannerAgent
from app.agents.researcher import ResearchAgent
from app.agents.risk_analyzer import RiskAnalysisAgent
from app.agents.startup_creation import StartupCreationAgent
from app.agents.state import AgentState
from app.memory.langgraph_checkpoint import get_langgraph_checkpointer
from app.memory.long_term_store import LongTermMemoryStore
from app.memory.short_term import ShortTermMemoryStore
from app.models.llm import LLMService
from app.tools.scraper import ScraperTool
from app.tools.search_tool import SearchTool


class AgentGraphService:
    def __init__(self) -> None:
        short_term_memory = ShortTermMemoryStore()
        long_term_memory = LongTermMemoryStore()
        llm = LLMService()
        search_tool = SearchTool()
        scraper = ScraperTool()

        self.coordinator = CoordinatorAgent(
            short_term_memory=short_term_memory,
            long_term_memory=long_term_memory,
        )
        self.planner = PlannerAgent(llm=llm)
        self.researcher = ResearchAgent(search_tool=search_tool, scraper=scraper)
        self.market_analyzer = MarketAnalysisAgent(llm=llm)
        self.financial_analyzer = FinancialAnalysisAgent(llm=llm)
        self.risk_analyzer = RiskAnalysisAgent(llm=llm)
        self.decision = DecisionAgent(llm=llm)
        self.startup_creation = StartupCreationAgent(llm=llm)
        self.evaluator = EvaluationAgent()

        graph = StateGraph(AgentState)
        graph.add_node("coordinator_pre", self.coordinator.pre_run)
        graph.add_node("planner", self.planner.run)
        graph.add_node("researcher", self.researcher.run)
        graph.add_node("market", self.market_analyzer.run)
        graph.add_node("financial", self.financial_analyzer.run)
        graph.add_node("risk", self.risk_analyzer.run)
        graph.add_node("decision", self.decision.run)
        graph.add_node("startup_creation", self.startup_creation.run)
        graph.add_node("evaluate", self.evaluator.run)
        graph.add_node("coordinator_post", self.coordinator.post_run)

        graph.set_entry_point("coordinator_pre")
        graph.add_edge("coordinator_pre", "planner")
        graph.add_conditional_edges(
            "planner",
            self._route_after_planner,
            {
                "startup_creation": "researcher",
                "investment_analysis": "researcher",
            },
        )
        graph.add_conditional_edges(
            "researcher",
            self._route_after_research,
            {
                "startup_creation": "startup_creation",
                "investment_analysis": "market",
            },
        )
        graph.add_edge("market", "financial")
        graph.add_edge("financial", "risk")
        graph.add_edge("risk", "decision")
        graph.add_edge("startup_creation", "evaluate")
        graph.add_edge("decision", "evaluate")
        graph.add_edge("evaluate", "coordinator_post")
        graph.add_edge("coordinator_post", END)

        self.app = graph.compile(checkpointer=get_langgraph_checkpointer())

    @staticmethod
    def _route_after_planner(state: AgentState) -> str:
        route = state.get("route", "startup_investment")
        if route == "startup_creation":
            return "startup_creation"
        return "investment_analysis"

    @staticmethod
    def _route_after_research(state: AgentState) -> str:
        route = state.get("route", "startup_investment")
        if route == "startup_creation":
            return "startup_creation"
        return "investment_analysis"

    def run(
        self,
        session_id: str,
        query: str,
        route: str = "startup_investment",
        in_scope: bool = True,
        policy_message: str = "Query matches startup investment analysis domain.",
    ) -> AgentState:
        initial_state: AgentState = {
            "session_id": session_id,
            "query": query,
            "route": route,
            "in_scope": in_scope,
            "policy_message": policy_message,
            "trace_id": str(uuid4()),
            "sources": [],
            "tasks": [],
        }
        config = {"configurable": {"thread_id": session_id}}
        result = self.app.invoke(initial_state, config=config)
        return result
