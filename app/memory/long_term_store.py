import json
import sqlite3
from pathlib import Path

from app.config.settings import get_settings


class LongTermMemoryStore:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._memory: dict[str, dict[str, object]] = {}
        self._use_sqlite = self.settings.memory_backend.lower() == "sqlite"
        self._db_path = Path(self.settings.memory_db_path)
        if self._use_sqlite:
            self._db_path.parent.mkdir(parents=True, exist_ok=True)
            self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS long_term_kv (
                    session_id TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value_json TEXT NOT NULL,
                    PRIMARY KEY (session_id, key)
                )
                """
            )
            conn.commit()

    def upsert(self, session_id: str, key: str, value: object) -> None:
        if self._use_sqlite:
            with sqlite3.connect(self._db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO long_term_kv(session_id, key, value_json)
                    VALUES(?, ?, ?)
                    ON CONFLICT(session_id, key) DO UPDATE SET value_json = excluded.value_json
                    """,
                    (session_id, key, json.dumps(value)),
                )
                conn.commit()
            return
        self._memory.setdefault(session_id, {})
        self._memory[session_id][key] = value

    def get(self, session_id: str, key: str, default: object = None) -> object:
        if self._use_sqlite:
            with sqlite3.connect(self._db_path) as conn:
                row = conn.execute(
                    "SELECT value_json FROM long_term_kv WHERE session_id = ? AND key = ?",
                    (session_id, key),
                ).fetchone()
            if not row:
                return default
            try:
                return json.loads(row[0])
            except Exception:
                return default
        return self._memory.get(session_id, {}).get(key, default)

    def get_all(self, session_id: str) -> dict[str, object]:
        if self._use_sqlite:
            with sqlite3.connect(self._db_path) as conn:
                rows = conn.execute(
                    "SELECT key, value_json FROM long_term_kv WHERE session_id = ?",
                    (session_id,),
                ).fetchall()
            out: dict[str, object] = {}
            for key, value_json in rows:
                try:
                    out[key] = json.loads(value_json)
                except Exception:
                    continue
            return out
        return self._memory.get(session_id, {})
