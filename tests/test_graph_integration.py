from app.agents.graph import AgentGraphService


def test_graph_follow_up_reuses_memory_context(monkeypatch) -> None:
    service = AgentGraphService()

    def fake_research(state):
        state["search_results"] = [{"url": "https://x.example"}]
        state["documents"] = [{"source": "https://x.example", "content": "India EV market"}]
        state["retrieved_context"] = [{"content": "India EV market", "source": "https://x.example", "score": 0.7}]
        state["sources"] = ["https://x.example"]
        return state

    monkeypatch.setattr(service.researcher, "run", fake_research)
    monkeypatch.setattr(service.decision.llm, "summarize", lambda prompt: "Final answer")

    session_id = "it-session-1"
    first = service.run(session_id=session_id, query="Analyze India EV startups")
    assert first["final_answer"] == "Final answer"

    second = service.run(session_id=session_id, query="Now compare with US EV startups")
    # Coordinator should add follow-up merge task once history exists.
    assert "follow_up_context_merge" in second.get("tasks", [])
