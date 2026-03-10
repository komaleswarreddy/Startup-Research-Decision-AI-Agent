import os
from dataclasses import dataclass, field
from functools import lru_cache

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    groq_api_key: str = field(default_factory=lambda: os.getenv("GROQ_API_KEY", ""))
    groq_model: str = field(
        default_factory=lambda: os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    )
    tavily_api_key: str = field(default_factory=lambda: os.getenv("TAVILY_API_KEY", ""))
    langsmith_api_key: str = field(default_factory=lambda: os.getenv("LANGSMITH_API_KEY", ""))
    langsmith_project: str = field(
        default_factory=lambda: os.getenv("LANGSMITH_PROJECT", "startup-research-agent")
    )
    langchain_tracing_v2: str = field(
        default_factory=lambda: os.getenv("LANGCHAIN_TRACING_V2", "true")
    )
    otel_exporter_otlp_endpoint: str = field(
        default_factory=lambda: os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318")
    )
    otel_service_name: str = field(
        default_factory=lambda: os.getenv("OTEL_SERVICE_NAME", "startup-research-agent")
    )
    memory_backend: str = field(default_factory=lambda: os.getenv("MEMORY_BACKEND", "inmemory"))
    memory_db_path: str = field(default_factory=lambda: os.getenv("MEMORY_DB_PATH", "artifacts/memory.db"))
    checkpoint_backend: str = field(
        default_factory=lambda: os.getenv("CHECKPOINT_BACKEND", "memory")
    )
    checkpoint_db_path: str = field(
        default_factory=lambda: os.getenv("CHECKPOINT_DB_PATH", "artifacts/checkpoint.db")
    )
    llm_max_retries: int = field(default_factory=lambda: int(os.getenv("LLM_MAX_RETRIES", "2")))
    llm_retry_base_seconds: float = field(
        default_factory=lambda: float(os.getenv("LLM_RETRY_BASE_SECONDS", "0.5"))
    )
    tool_max_retries: int = field(default_factory=lambda: int(os.getenv("TOOL_MAX_RETRIES", "2")))
    tool_retry_base_seconds: float = field(
        default_factory=lambda: float(os.getenv("TOOL_RETRY_BASE_SECONDS", "0.5"))
    )
    tool_circuit_breaker_failures: int = field(
        default_factory=lambda: int(os.getenv("TOOL_CIRCUIT_BREAKER_FAILURES", "3"))
    )
    tool_circuit_breaker_seconds: int = field(
        default_factory=lambda: int(os.getenv("TOOL_CIRCUIT_BREAKER_SECONDS", "30"))
    )
    python_exec_timeout_seconds: float = field(
        default_factory=lambda: float(os.getenv("PYTHON_EXEC_TIMEOUT_SECONDS", "2"))
    )
    python_exec_max_code_chars: int = field(
        default_factory=lambda: int(os.getenv("PYTHON_EXEC_MAX_CODE_CHARS", "4000"))
    )
    rag_vector_backend: str = field(default_factory=lambda: os.getenv("RAG_VECTOR_BACKEND", "chroma"))
    rag_chroma_path: str = field(default_factory=lambda: os.getenv("RAG_CHROMA_PATH", "artifacts/chroma"))
    rag_collection_name: str = field(default_factory=lambda: os.getenv("RAG_COLLECTION_NAME", "startup_docs"))
    rag_embedding_model: str = field(
        default_factory=lambda: os.getenv("RAG_EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
    )
    rag_reranker_model: str = field(
        default_factory=lambda: os.getenv("RAG_RERANKER_MODEL", "BAAI/bge-reranker-base")
    )
    rag_top_k: int = field(default_factory=lambda: int(os.getenv("RAG_TOP_K", "6")))
    rag_retrieve_pool_k: int = field(default_factory=lambda: int(os.getenv("RAG_RETRIEVE_POOL_K", "12")))
    rag_chunk_size: int = field(default_factory=lambda: int(os.getenv("RAG_CHUNK_SIZE", "900")))
    rag_chunk_overlap: int = field(default_factory=lambda: int(os.getenv("RAG_CHUNK_OVERLAP", "120")))
    rag_enable_reranker: bool = field(
        default_factory=lambda: os.getenv("RAG_ENABLE_RERANKER", "false").lower() == "true"
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
