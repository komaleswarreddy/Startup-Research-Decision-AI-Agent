from dataclasses import dataclass
import hashlib
import logging
from pathlib import Path

from app.config.settings import get_settings

logger = logging.getLogger(__name__)

@dataclass
class StoredDocument:
    content: str
    source: str
    title: str = ""
    doc_id: str = ""


class InMemoryVectorStore:
    def __init__(self) -> None:
        self._docs: list[StoredDocument] = []

    def add_documents(self, docs: list[StoredDocument]) -> None:
        self._docs.extend(docs)

    def all_documents(self) -> list[StoredDocument]:
        return list(self._docs)

    def supports_semantic(self) -> bool:
        return False


class ChromaVectorStore:
    """Best-effort Chroma store with graceful fallback to in-memory storage."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self._fallback = InMemoryVectorStore()
        self._collection = None
        self._client = None
        self._init_client()

    def _init_client(self) -> None:
        try:
            import chromadb
            from chromadb.config import Settings as ChromaSettings

            persist_path = Path(self.settings.rag_chroma_path)
            persist_path.mkdir(parents=True, exist_ok=True)
            self._client = chromadb.PersistentClient(
                path=str(persist_path),
                settings=ChromaSettings(anonymized_telemetry=False),
            )
            self._collection = self._client.get_or_create_collection(
                name=self.settings.rag_collection_name
            )
            logger.info(
                "Chroma vector store initialized successfully at %s (collection=%s)",
                str(persist_path),
                self.settings.rag_collection_name,
            )
        except Exception as exc:
            logger.warning("Chroma init failed, falling back to in-memory store: %s", exc)
            self._client = None
            self._collection = None

    @staticmethod
    def _stable_id(doc: StoredDocument) -> str:
        seed = f"{doc.source}|{doc.title}|{doc.content}".encode("utf-8")
        return hashlib.sha256(seed).hexdigest()[:24]

    def add_documents(self, docs: list[StoredDocument]) -> None:
        if not docs:
            return
        self._fallback.add_documents(docs)
        if not self._collection:
            return
        try:
            ids = []
            documents = []
            metadatas = []
            for doc in docs:
                doc_id = doc.doc_id or self._stable_id(doc)
                ids.append(doc_id)
                documents.append(doc.content)
                metadatas.append({"source": doc.source, "title": doc.title})
            self._collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
        except Exception as exc:
            logger.warning("Chroma upsert failed: %s", exc)

    def all_documents(self) -> list[StoredDocument]:
        return self._fallback.all_documents()

    def similarity_search(
        self, query: str, top_k: int, query_embedding: list[float] | None
    ) -> list[StoredDocument]:
        if not self._collection or not query_embedding:
            return []
        try:
            result = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["documents", "metadatas"],
            )
            docs = result.get("documents", [[]])[0]
            metas = result.get("metadatas", [[]])[0]
            out: list[StoredDocument] = []
            for content, meta in zip(docs, metas):
                out.append(
                    StoredDocument(
                        content=str(content),
                        source=str((meta or {}).get("source", "unknown")),
                        title=str((meta or {}).get("title", "")),
                    )
                )
            return out
        except Exception as exc:
            logger.warning("Chroma query failed: %s", exc)
            return []

    def supports_semantic(self) -> bool:
        return self._collection is not None
