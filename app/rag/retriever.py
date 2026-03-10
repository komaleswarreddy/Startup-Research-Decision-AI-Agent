import re
from dataclasses import dataclass
import logging

from app.config.settings import get_settings
from app.rag.vector_store import ChromaVectorStore, InMemoryVectorStore, StoredDocument

logger = logging.getLogger(__name__)


@dataclass
class RetrievedDocument:
    content: str
    source: str
    score: float


class EmbeddingService:
    _shared_model = None
    _shared_load_attempted = False

    def __init__(self) -> None:
        self.settings = get_settings()
        self._model = None
        self._load_attempted = False

    @property
    def enabled(self) -> bool:
        self._ensure_loaded()
        return self._model is not None

    def _ensure_loaded(self) -> None:
        if EmbeddingService._shared_model is not None:
            self._model = EmbeddingService._shared_model
            self._load_attempted = True
            return
        if EmbeddingService._shared_load_attempted:
            self._model = None
            self._load_attempted = True
            return
        if self._load_attempted:
            return
        self._load_attempted = True
        EmbeddingService._shared_load_attempted = True
        try:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.settings.rag_embedding_model)
            EmbeddingService._shared_model = self._model
        except Exception as exc:
            logger.warning("Embedding model unavailable, using lexical retrieval: %s", exc)
            self._model = None

    def embed_query(self, text: str) -> list[float] | None:
        self._ensure_loaded()
        if not self.enabled:
            return None
        try:
            vector = self._model.encode([text], normalize_embeddings=True)[0]
            return [float(v) for v in vector.tolist()]
        except Exception as exc:
            logger.warning("Query embedding failed: %s", exc)
            return None

    def score_pair(self, query: str, doc: str) -> float:
        self._ensure_loaded()
        if not self.enabled:
            return 0.0
        try:
            embeddings = self._model.encode([query, doc], normalize_embeddings=True)
            q = embeddings[0]
            d = embeddings[1]
            return float((q @ d))
        except Exception:
            return 0.0

    def score_documents(self, query: str, docs: list[str]) -> list[float]:
        self._ensure_loaded()
        if not self.enabled or not docs:
            return [0.0 for _ in docs]
        try:
            embeddings = self._model.encode([query, *docs], normalize_embeddings=True)
            q = embeddings[0]
            scores: list[float] = []
            for vec in embeddings[1:]:
                scores.append(float(q @ vec))
            return scores
        except Exception:
            return [0.0 for _ in docs]


class RerankerService:
    _shared_model = None
    _shared_load_attempted = False

    def __init__(self) -> None:
        self.settings = get_settings()
        self._model = None
        self._load_attempted = False
        if not self.settings.rag_enable_reranker:
            return

    @property
    def enabled(self) -> bool:
        self._ensure_loaded()
        return self._model is not None

    def _ensure_loaded(self) -> None:
        if RerankerService._shared_model is not None:
            self._model = RerankerService._shared_model
            self._load_attempted = True
            return
        if RerankerService._shared_load_attempted:
            self._model = None
            self._load_attempted = True
            return
        if self._load_attempted or not self.settings.rag_enable_reranker:
            return
        self._load_attempted = True
        RerankerService._shared_load_attempted = True
        try:
            from sentence_transformers import CrossEncoder

            self._model = CrossEncoder(self.settings.rag_reranker_model)
            RerankerService._shared_model = self._model
        except Exception as exc:
            logger.warning("Reranker unavailable, ranking by retrieval score: %s", exc)
            self._model = None

    def rerank(self, query: str, docs: list[RetrievedDocument]) -> list[RetrievedDocument]:
        self._ensure_loaded()
        if not self.enabled or not docs:
            return docs
        pairs = [(query, d.content) for d in docs]
        try:
            scores = self._model.predict(pairs)
            rescored: list[RetrievedDocument] = []
            for doc, score in zip(docs, scores):
                rescored.append(
                    RetrievedDocument(content=doc.content, source=doc.source, score=float(score))
                )
            rescored.sort(key=lambda x: x.score, reverse=True)
            return rescored
        except Exception as exc:
            logger.warning("Reranker failed: %s", exc)
            return docs


class Retriever:
    def __init__(self, store: InMemoryVectorStore | ChromaVectorStore) -> None:
        self.store = store
        self.settings = get_settings()
        self.embedder = EmbeddingService()
        self.reranker = RerankerService()

    @staticmethod
    def _tokenize(text: str) -> set[str]:
        return set(re.findall(r"[a-zA-Z0-9]+", text.lower()))

    def retrieve(self, query: str, top_k: int = 5) -> list[RetrievedDocument]:
        if (
            hasattr(self.store, "similarity_search")
            and getattr(self.store, "supports_semantic", lambda: False)()
            and self.embedder.enabled
        ):
            query_embedding = self.embedder.embed_query(query)
            semantic_docs = self.store.similarity_search(
                query=query,
                top_k=max(top_k, self.settings.rag_retrieve_pool_k),
                query_embedding=query_embedding,
            )
            if semantic_docs:
                total = max(1, len(semantic_docs))
                semantic_results = [
                    RetrievedDocument(
                        content=doc.content,
                        source=doc.source,
                        # Chroma already performed nearest-neighbor ranking.
                        # Use rank-based scores to avoid redundant per-doc embedding passes.
                        score=round(1.0 - (idx / total), 4),
                    )
                    for idx, doc in enumerate(semantic_docs)
                ]
                ranked = self.reranker.rerank(query, semantic_results)
                return ranked[:top_k]

        query_tokens = self._tokenize(query)
        results: list[RetrievedDocument] = []

        for doc in self.store.all_documents():
            doc_tokens = self._tokenize(doc.content)
            if not doc_tokens:
                continue
            overlap = len(query_tokens.intersection(doc_tokens))
            score = overlap / max(1, len(query_tokens))
            if score > 0:
                results.append(
                    RetrievedDocument(content=doc.content, source=doc.source, score=score)
                )

        results.sort(key=lambda item: item.score, reverse=True)
        return results[:top_k]

    @staticmethod
    def from_raw_documents(raw_docs: list[dict[str, str]]) -> list[StoredDocument]:
        docs: list[StoredDocument] = []
        for item in raw_docs:
            docs.append(
                StoredDocument(
                    content=item.get("content", ""),
                    source=item.get("source", "unknown"),
                    title=item.get("title", ""),
                )
            )
        return docs
