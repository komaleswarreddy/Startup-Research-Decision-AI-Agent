from app.config.settings import get_settings
from app.rag.vector_store import StoredDocument


def dedupe_and_chunk(raw_docs: list[dict[str, str]]) -> list[StoredDocument]:
    settings = get_settings()
    chunk_size = max(200, settings.rag_chunk_size)
    overlap = max(0, min(settings.rag_chunk_overlap, chunk_size // 2))

    seen: set[tuple[str, str]] = set()
    output: list[StoredDocument] = []
    for raw in raw_docs:
        source = str(raw.get("source", "unknown"))
        title = str(raw.get("title", ""))
        content = str(raw.get("content", "")).strip()
        if not content:
            continue
        dedupe_key = (source, content[:500])
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)

        start = 0
        step = max(1, chunk_size - overlap)
        while start < len(content):
            chunk = content[start : start + chunk_size].strip()
            if chunk:
                output.append(StoredDocument(content=chunk, source=source, title=title))
            if start + chunk_size >= len(content):
                break
            start += step
    return output
