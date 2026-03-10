import logging
from pathlib import Path
from typing import Any

from app.config.settings import get_settings

logger = logging.getLogger(__name__)


def get_langgraph_checkpointer() -> Any:
    settings = get_settings()
    if settings.checkpoint_backend.lower() == "sqlite":
        db_path = Path(settings.checkpoint_db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            from langgraph.checkpoint.sqlite import SqliteSaver

            return SqliteSaver.from_conn_string(str(db_path))
        except Exception as exc:
            logger.warning("SQLite checkpointer unavailable, using memory saver: %s", exc)

    from langgraph.checkpoint.memory import MemorySaver

    return MemorySaver()
