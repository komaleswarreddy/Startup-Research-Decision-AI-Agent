from concurrent.futures import ThreadPoolExecutor

from fastapi.testclient import TestClient

from app.agents.graph import AgentGraphService
from app.memory.langgraph_checkpoint import get_langgraph_checkpointer
from main import app

client = TestClient(app)


def test_graph_run_returns_required_state_keys() -> None:
    service = AgentGraphService()
    result = service.run("contract-session", "Analyze Indian EV startups")
    required = {
        "route",
        "in_scope",
        "policy_message",
        "final_answer",
        "recommendation",
        "risk_level",
        "top_startup",
        "sources",
        "evaluation",
        "trace_id",
    }
    assert required.issubset(set(result.keys()))


def test_checkpointer_factory_returns_object() -> None:
    checkpointer = get_langgraph_checkpointer()
    assert checkpointer is not None


def test_api_can_handle_parallel_requests(monkeypatch) -> None:
    from app.api import routes

    def fake_run(
        session_id: str,
        query: str,
        route: str = "startup_investment",
        in_scope: bool = True,
        policy_message: str = "",
    ):
        return {
            "route": "startup_investment",
            "in_scope": True,
            "policy_message": "Query matches startup investment analysis domain.",
            "final_answer": f"ok-{session_id}",
            "recommendation": "Buy",
            "risk_level": "Medium",
            "top_startup": "Ather Energy",
            "sources": ["s1"],
            "evaluation": {"confidence_score": 0.8},
            "trace_id": "t-1",
        }

    monkeypatch.setattr(routes.graph_service, "run", fake_run)

    def _call(i: int):
        resp = client.post(
            "/query",
            json={"query": f"Analyze startup {i}", "session_id": f"s-{i}"},
        )
        return resp.status_code, resp.json()

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(_call, range(20)))

    assert all(code == 200 for code, _ in results)
    assert all("analysis" in body for _, body in results)
    assert all("route" in body for _, body in results)