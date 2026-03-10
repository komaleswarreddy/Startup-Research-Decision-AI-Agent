from app.config.settings import get_settings
from app.memory.long_term_store import LongTermMemoryStore
from app.memory.short_term import ShortTermMemoryStore


def test_sqlite_memory_persists_across_store_instances(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "memory.db"
    monkeypatch.setenv("MEMORY_BACKEND", "sqlite")
    monkeypatch.setenv("MEMORY_DB_PATH", str(db_path))
    get_settings.cache_clear()

    short_term_a = ShortTermMemoryStore()
    long_term_a = LongTermMemoryStore()
    short_term_a.add_message("s-1", "user", "first question")
    long_term_a.upsert("s-1", "last_analysis", "analysis A")

    short_term_b = ShortTermMemoryStore()
    long_term_b = LongTermMemoryStore()
    history = short_term_b.get_history("s-1")
    assert len(history) == 1
    assert history[0]["content"] == "first question"
    assert long_term_b.get("s-1", "last_analysis") == "analysis A"

    monkeypatch.delenv("MEMORY_BACKEND", raising=False)
    monkeypatch.delenv("MEMORY_DB_PATH", raising=False)
    get_settings.cache_clear()
