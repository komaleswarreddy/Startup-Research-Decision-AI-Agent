import logging
from time import sleep

from app.config.settings import get_settings

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._client = None
        if self.settings.groq_api_key:
            try:
                from langchain_groq import ChatGroq

                self._client = ChatGroq(
                    model=self.settings.groq_model,
                    api_key=self.settings.groq_api_key,
                    temperature=0.1,
                )
            except Exception as exc:
                logger.warning("Groq client init failed: %s", exc)

    def summarize(self, prompt: str) -> str:
        if not self._client:
            return (
                "Groq API key not configured. Returning fallback summary.\n\n"
                + prompt[:900]
            )

        retries = max(0, self.settings.llm_max_retries)
        for attempt in range(retries + 1):
            try:
                response = self._client.invoke(prompt)
                return str(response.content)
            except Exception as exc:
                logger.warning("Groq invoke failed (attempt %s): %s", attempt + 1, exc)
                if attempt >= retries:
                    return "LLM call failed. Fallback summary generated from available context."
                sleep(self.settings.llm_retry_base_seconds * (2**attempt))
        return "LLM call failed. Fallback summary generated from available context."
