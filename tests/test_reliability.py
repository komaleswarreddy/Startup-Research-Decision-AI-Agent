from app.config.settings import get_settings
from app.models.llm import LLMService
from app.tools.search_tool import SearchTool


class _FailingSearchClient:
    def __init__(self) -> None:
        self.calls = 0

    def search(self, query: str, search_depth: str, max_results: int):
        self.calls += 1
        raise RuntimeError("search fail")


class _FlakyLLMClient:
    def __init__(self) -> None:
        self.calls = 0

    def invoke(self, prompt: str):
        self.calls += 1
        if self.calls < 2:
            raise RuntimeError("transient")
        return type("Resp", (), {"content": "ok"})()


def test_search_tool_uses_fallback_after_retries(monkeypatch) -> None:
    monkeypatch.setenv("TOOL_MAX_RETRIES", "1")
    monkeypatch.setenv("TOOL_RETRY_BASE_SECONDS", "0")
    monkeypatch.setenv("TOOL_CIRCUIT_BREAKER_FAILURES", "1")
    monkeypatch.setenv("TOOL_CIRCUIT_BREAKER_SECONDS", "10")
    get_settings.cache_clear()

    tool = SearchTool()
    tool._client = _FailingSearchClient()  # type: ignore[attr-defined]
    result = tool.search("ev market")
    assert result == []

    # Circuit is now open and should short-circuit to fallback again.
    result2 = tool.search("ev market")
    assert result2 == []

    monkeypatch.delenv("TOOL_MAX_RETRIES", raising=False)
    monkeypatch.delenv("TOOL_RETRY_BASE_SECONDS", raising=False)
    monkeypatch.delenv("TOOL_CIRCUIT_BREAKER_FAILURES", raising=False)
    monkeypatch.delenv("TOOL_CIRCUIT_BREAKER_SECONDS", raising=False)
    get_settings.cache_clear()


def test_llm_service_retries_transient_failures(monkeypatch) -> None:
    monkeypatch.setenv("LLM_MAX_RETRIES", "2")
    monkeypatch.setenv("LLM_RETRY_BASE_SECONDS", "0")
    get_settings.cache_clear()

    llm = LLMService()
    llm._client = _FlakyLLMClient()  # type: ignore[attr-defined]
    assert llm.summarize("hello") == "ok"

    monkeypatch.delenv("LLM_MAX_RETRIES", raising=False)
    monkeypatch.delenv("LLM_RETRY_BASE_SECONDS", raising=False)
    get_settings.cache_clear()
