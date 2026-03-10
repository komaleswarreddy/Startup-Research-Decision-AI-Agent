from app.rag.retriever import Retriever
from app.rag.vector_store import InMemoryVectorStore, StoredDocument
from app.tools.python_exec import SafePythonExecutor, cagr, project_revenue
from app.tools.scraper import ScraperTool


def test_cagr_and_projection_helpers() -> None:
    assert round(cagr(100, 200, 5), 2) > 0
    assert cagr(0, 100, 5) == 0.0
    assert project_revenue(100, 10, 3) == [110.0, 121.0, 133.1]


def test_safe_python_executor_success_and_forbidden_constructs() -> None:
    executor = SafePythonExecutor()

    success = executor.execute(
        code="market_cagr = 21\ninvestment_recommendation = 'Buy'",
        context={},
    )
    assert success.success is True
    assert success.output["market_cagr"] == 21

    forbidden = executor.execute(code="import os\nx = 1", context={})
    assert forbidden.success is False
    assert "Forbidden" in forbidden.error


def test_safe_python_executor_runtime_error_is_captured() -> None:
    executor = SafePythonExecutor()
    result = executor.execute(code="x = 1 / 0", context={})
    assert result.success is False
    assert "division by zero" in result.error


def test_safe_python_executor_rejects_forbidden_name_usage() -> None:
    executor = SafePythonExecutor()
    result = executor.execute(code="x = eval('1+1')", context={})
    assert result.success is False
    assert "Forbidden name" in result.error


def test_safe_python_executor_timeout(monkeypatch) -> None:
    monkeypatch.setenv("PYTHON_EXEC_TIMEOUT_SECONDS", "0.1")
    from app.config.settings import get_settings

    get_settings.cache_clear()
    executor = SafePythonExecutor()
    result = executor.execute(code="while True:\n    pass", context={})
    assert result.success is False
    assert "timed out" in result.error.lower()
    monkeypatch.delenv("PYTHON_EXEC_TIMEOUT_SECONDS", raising=False)
    get_settings.cache_clear()


def test_retriever_scores_and_limits_results() -> None:
    store = InMemoryVectorStore()
    store.add_documents(
        [
            StoredDocument(content="Indian EV startup growth and charging expansion", source="a"),
            StoredDocument(content="US SaaS valuation reset with lower multiples", source="b"),
            StoredDocument(content="India EV subsidies and battery policy", source="c"),
        ]
    )
    retriever = Retriever(store)
    results = retriever.retrieve("India EV growth policy", top_k=2)

    assert len(results) == 2
    assert results[0].score >= results[1].score
    assert all(item.score > 0 for item in results)


def test_retriever_returns_empty_when_no_overlap() -> None:
    store = InMemoryVectorStore()
    store.add_documents([StoredDocument(content="healthcare genomics", source="x")])
    retriever = Retriever(store)
    assert retriever.retrieve("electric vehicles battery", top_k=5) == []


def test_scraper_enrich_uses_fallback_content_without_url() -> None:
    scraper = ScraperTool()
    docs = scraper.enrich_results(
        [{"title": "t", "url": "", "content": "fallback content for doc"}]
    )
    assert docs[0]["source"] == "unknown"
    assert "fallback content" in docs[0]["content"]

