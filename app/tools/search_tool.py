import logging
from time import sleep

from app.config.settings import get_settings
from app.tools.resilience import CircuitBreaker

logger = logging.getLogger(__name__)


class SearchTool:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._client = None
        self._breaker = CircuitBreaker(
            failure_threshold=self.settings.tool_circuit_breaker_failures,
            reset_timeout_seconds=self.settings.tool_circuit_breaker_seconds,
        )
        if self.settings.tavily_api_key:
            try:
                from tavily import TavilyClient

                self._client = TavilyClient(api_key=self.settings.tavily_api_key)
            except Exception as exc:
                logger.warning("Tavily init failed: %s", exc)

    def search(self, query: str, max_results: int = 5) -> list[dict[str, str]]:
        if not self._breaker.allow_request():
            logger.warning("Search circuit breaker open; fallback result used")
            return self._fallback_result()
        if not self._client:
            return self._fallback_result()

        retries = max(0, self.settings.tool_max_retries)
        for attempt in range(retries + 1):
            try:
                response = self._client.search(
                    query=query,
                    search_depth="basic",
                    max_results=max_results,
                )
                self._breaker.on_success()
                return response.get("results", [])
            except Exception as exc:
                logger.warning("Tavily search failed (attempt %s): %s", attempt + 1, exc)
                if attempt >= retries:
                    self._breaker.on_failure()
                    return self._fallback_result()
                sleep(self.settings.tool_retry_base_seconds * (2**attempt))
        return self._fallback_result()

    @staticmethod
    def _fallback_result() -> list[dict[str, str]]:
        return []
