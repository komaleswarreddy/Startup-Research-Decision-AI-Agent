from dataclasses import dataclass, field
import sqlite3
from pathlib import Path

from app.config.settings import get_settings

@dataclass
class SessionMemory:
    history: list[dict[str, str]] = field(default_factory=list)


class ShortTermMemoryStore:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._sessions: dict[str, SessionMemory] = {}
        self._use_sqlite = self.settings.memory_backend.lower() == "sqlite"
        self._db_path = Path(self.settings.memory_db_path)
        if self._use_sqlite:
            self._db_path.parent.mkdir(parents=True, exist_ok=True)
            self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS short_term_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def add_message(self, session_id: str, role: str, content: str) -> None:
        if self._use_sqlite:
            with sqlite3.connect(self._db_path) as conn:
                conn.execute(
                    "INSERT INTO short_term_messages(session_id, role, content) VALUES(?, ?, ?)",
                    (session_id, role, content),
                )
                conn.commit()
            return
        session = self._sessions.setdefault(session_id, SessionMemory())
        session.history.append({"role": role, "content": content})

    def get_history(self, session_id: str) -> list[dict[str, str]]:
        if self._use_sqlite:
            with sqlite3.connect(self._db_path) as conn:
                rows = conn.execute(
                    "SELECT role, content FROM short_term_messages WHERE session_id = ? ORDER BY id ASC",
                    (session_id,),
                ).fetchall()
            return [{"role": row[0], "content": row[1]} for row in rows]
        return self._sessions.get(session_id, SessionMemory()).history
