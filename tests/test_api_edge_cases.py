from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_query_validation_rejects_too_short_prompt() -> None:
    response = client.post("/query", json={"query": "hi"})
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "validation_error"
    assert "details" in body["error"]


def test_query_generates_session_id_when_missing(monkeypatch) -> None:
    from app.api import routes

    captured: dict[str, str] = {}

    def fake_run(
        session_id: str,
        query: str,
        route: str = "startup_investment",
        in_scope: bool = True,
        policy_message: str = "",
    ) -> dict[str, object]:
        captured["session_id"] = session_id
        captured["query"] = query
        return {
            "final_answer": "ok",
            "recommendation": "Buy",
            "risk_level": "Medium",
            "top_startup": "Ather Energy",
            "sources": ["s1"],
            "evaluation": {"confidence_score": 0.8},
            "trace_id": "trace-x",
        }

    monkeypatch.setattr(routes.graph_service, "run", fake_run)
    response = client.post("/query", json={"query": "Analyze EV startups deeply"})
    assert response.status_code == 200
    body = response.json()
    assert captured["query"] == "Analyze EV startups deeply"
    assert captured["session_id"].startswith("session-")
    assert body["trace_id"] == "trace-x"


def test_query_uses_provided_session_id(monkeypatch) -> None:
    from app.api import routes

    captured: dict[str, str] = {}

    def fake_run(
        session_id: str,
        query: str,
        route: str = "startup_investment",
        in_scope: bool = True,
        policy_message: str = "",
    ) -> dict[str, object]:
        captured["session_id"] = session_id
        return {
            "final_answer": "done",
            "recommendation": "Hold",
            "risk_level": "High",
            "top_startup": "Unknown",
            "sources": [],
            "evaluation": {},
            "trace_id": "trace-y",
        }

    monkeypatch.setattr(routes.graph_service, "run", fake_run)
    response = client.post(
        "/query",
        json={"query": "Analyze risks in seed startups", "session_id": "custom-session-9"},
    )
    assert response.status_code == 200
    assert captured["session_id"] == "custom-session-9"


def test_startup_creation_route_is_forwarded_to_graph(monkeypatch) -> None:
    from app.api import routes
    from app.agents.intent_router import IntentResult

    captured: dict[str, str] = {}

    def fake_classify(query: str) -> IntentResult:
        return IntentResult(
            route="startup_creation",
            in_scope=True,
            reason="creation flow",
            confidence=0.9,
        )

    def fake_run(
        session_id: str,
        query: str,
        route: str = "startup_investment",
        in_scope: bool = True,
        policy_message: str = "",
    ) -> dict[str, object]:
        captured["route"] = route
        return {
            "final_answer": "creation guide",
            "recommendation": "N/A",
            "risk_level": "N/A",
            "top_startup": "N/A",
            "sources": ["s1"],
            "evaluation": {"confidence_score": 0.9},
            "trace_id": "trace-z",
        }

    monkeypatch.setattr(routes.intent_router, "classify", fake_classify)
    monkeypatch.setattr(routes.graph_service, "run", fake_run)
    response = client.post("/query", json={"query": "How to start startup in india?"})
    assert response.status_code == 200
    body = response.json()
    assert captured["route"] == "startup_creation"
    assert body["recommendation"] == "N/A"
    assert body["route"] == "startup_creation"


def test_startup_creation_safety_override_wins_even_if_classifier_misfires(monkeypatch) -> None:
    from app.api import routes
    from app.agents.intent_router import IntentResult

    captured: dict[str, str] = {}

    def fake_classify(query: str) -> IntentResult:
        return IntentResult(
            route="startup_investment",
            in_scope=True,
            reason="misclassified",
            confidence=0.95,
        )

    def fake_run(
        session_id: str,
        query: str,
        route: str = "startup_investment",
        in_scope: bool = True,
        policy_message: str = "",
    ) -> dict[str, object]:
        captured["route"] = route
        return {
            "final_answer": "creation guide",
            "recommendation": "N/A",
            "risk_level": "N/A",
            "top_startup": "N/A",
            "sources": [],
            "evaluation": {"confidence_score": 0.9},
            "trace_id": "trace-safe",
        }

    monkeypatch.setattr(routes.intent_router, "classify", fake_classify)
    monkeypatch.setattr(routes.graph_service, "run", fake_run)
    response = client.post("/query", json={"query": "How to start startup in india?"})
    assert response.status_code == 200
    body = response.json()
    assert captured["route"] == "startup_creation"
    assert body["route"] == "startup_creation"


def test_query_failure_returns_standard_error_envelope(monkeypatch) -> None:
    from app.api import routes

    def fail_run(
        session_id: str,
        query: str,
        route: str = "startup_investment",
        in_scope: bool = True,
        policy_message: str = "",
    ) -> dict[str, object]:
        raise RuntimeError("graph crashed")

    monkeypatch.setattr(routes.graph_service, "run", fail_run)
    response = client.post("/query", json={"query": "Analyze startup failure path"})
    assert response.status_code == 500
    body = response.json()
    assert "error" in body
    assert body["error"]["code"] == "query_processing_failed"
    assert "Unable to process query" in body["error"]["message"]


def test_out_of_scope_query_is_rejected_without_graph_execution(monkeypatch) -> None:
    from app.api import routes

    def fail_if_called(
        session_id: str,
        query: str,
        route: str = "startup_investment",
        in_scope: bool = True,
        policy_message: str = "",
    ) -> dict[str, object]:
        raise AssertionError("Graph should not run for out-of-scope query")

    monkeypatch.setattr(routes.graph_service, "run", fail_if_called)
    response = client.post("/query", json={"query": "who is cm of andhra pradesh"})
    assert response.status_code == 200
    body = response.json()
    assert body["in_scope"] is False
    assert body["route"] == "out_of_scope"
    assert body["recommendation"] == "N/A"
    assert "specialized for startup research" in body["policy_message"]


def test_self_intro_query_is_out_of_scope(monkeypatch) -> None:
    from app.api import routes

    def fail_if_called(
        session_id: str,
        query: str,
        route: str = "startup_investment",
        in_scope: bool = True,
        policy_message: str = "",
    ) -> dict[str, object]:
        raise AssertionError("Graph should not run for out-of-scope query")

    monkeypatch.setattr(routes.graph_service, "run", fail_if_called)
    response = client.post("/query", json={"query": "my name is komal"})
    assert response.status_code == 200
    body = response.json()
    assert body["in_scope"] is False
    assert body["route"] == "out_of_scope"
    assert body["top_startup"] == "N/A"
