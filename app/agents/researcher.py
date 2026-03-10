from app.agents.state import AgentState
from app.config.settings import get_settings
from app.rag.chunking import dedupe_and_chunk
from app.rag.retriever import Retriever
from app.rag.vector_store import ChromaVectorStore, InMemoryVectorStore
from app.tools.scraper import ScraperTool
from app.tools.search_tool import SearchTool


class ResearchAgent:
    def __init__(self, search_tool: SearchTool, scraper: ScraperTool) -> None:
        settings = get_settings()
        self.search_tool = search_tool
        self.scraper = scraper
        if settings.rag_vector_backend.lower() == "chroma":
            self.store = ChromaVectorStore()
        else:
            self.store = InMemoryVectorStore()
        self.retriever = Retriever(self.store)
        self.settings = settings

    def run(self, state: AgentState) -> AgentState:
        query = state.get("query", "")
        route = state.get("route", "")
        max_results = 3 if route == "startup_creation" else 5
        search_results = self.search_tool.search(query=query, max_results=max_results)

        # Fast path for startup-creation guidance: rely on search snippets first
        # to avoid slow multi-page scraping on CPU-bound environments.
        if route == "startup_creation":
            docs = [
                {
                    "source": str(item.get("url", "unknown")),
                    "title": str(item.get("title", "")),
                    "content": str(item.get("content", "")).strip() or str(item.get("title", "")),
                }
                for item in search_results
            ]
        else:
            docs = self.scraper.enrich_results(search_results)
        chunked_docs = dedupe_and_chunk(docs)
        self.store.add_documents(chunked_docs)

        retrieved = self.retriever.retrieve(query=query, top_k=self.settings.rag_top_k)
        filtered = [item for item in retrieved if item.score >= 0.12]
        selected = filtered[: self.settings.rag_top_k] if filtered else retrieved[: self.settings.rag_top_k]
        if not selected:
            # Fallback for sparse hits: keep first docs to preserve explainability.
            selected = [
                type("Doc", (), {"content": doc.get("content", ""), "source": doc.get("source", "unknown"), "score": 0.2})()
                for doc in docs[:3]
            ]

        state["search_results"] = search_results
        state["documents"] = docs
        state["retrieved_context"] = [
            {"content": item.content, "source": item.source, "score": item.score}
            for item in selected
        ]
        unique_sources: list[str] = []
        for item in selected:
            if item.source and item.source not in unique_sources:
                unique_sources.append(item.source)
        if not unique_sources:
            for item in search_results:
                src = str(item.get("url", ""))
                if src and src not in unique_sources:
                    unique_sources.append(src)
        state["sources"] = unique_sources[:5]
        return state
