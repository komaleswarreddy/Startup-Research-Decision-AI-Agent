from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_query_endpoint_contract() -> None:
    response = client.post(
        "/query",
        json={
            "query": "Analyze Indian EV startups and recommend top opportunities",
            "session_id": "test-session-1",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "route" in data
    assert "in_scope" in data
    assert "policy_message" in data
    assert "analysis" in data
    assert "recommendation" in data
    assert "risk_level" in data
    assert "top_startup" in data
    assert "sources" in data
    assert "evaluation" in data
    assert "trace_id" in data
