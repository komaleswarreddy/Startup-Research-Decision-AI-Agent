from typing import Any
from time import sleep

import requests
from bs4 import BeautifulSoup

from app.config.settings import get_settings
from app.tools.resilience import CircuitBreaker


class ScraperTool:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._breaker = CircuitBreaker(
            failure_threshold=self.settings.tool_circuit_breaker_failures,
            reset_timeout_seconds=self.settings.tool_circuit_breaker_seconds,
        )

    def scrape_text(self, url: str) -> str:
        if not self._breaker.allow_request():
            return ""
        retries = max(0, self.settings.tool_max_retries)
        for attempt in range(retries + 1):
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "html.parser")
                self._breaker.on_success()
                return " ".join(soup.get_text(separator=" ").split())[:3000]
            except Exception:
                if attempt >= retries:
                    self._breaker.on_failure()
                    return ""
                sleep(self.settings.tool_retry_base_seconds * (2**attempt))
        return ""

    def enrich_results(self, search_results: list[dict[str, Any]]) -> list[dict[str, str]]:
        docs: list[dict[str, str]] = []
        for item in search_results:
            url = str(item.get("url", ""))
            content = str(item.get("content", "")).strip()
            page_text = self.scrape_text(url) if url else ""
            docs.append(
                {
                    "source": url or "unknown",
                    "title": str(item.get("title", "")),
                    "content": page_text or content or str(item.get("title", "")),
                }
            )
        return docs
