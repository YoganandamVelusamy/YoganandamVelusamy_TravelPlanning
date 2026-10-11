from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator


class FeedbackStore:
    def __init__(self, database_path: Path | str) -> None:
        self._database_path = Path(database_path)
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    experience_id TEXT NOT NULL,
                    rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
                    comment TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL
                )
                """
            )

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self._database_path)
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def save(self, experience_id: str, rating: int, comment: str = "") -> int:
        with self._connect() as connection:
            cursor = connection.execute(
                "INSERT INTO feedback (experience_id, rating, comment, created_at) VALUES (?, ?, ?, ?)",
                (experience_id, rating, comment, datetime.now(timezone.utc).isoformat()),
            )
            return int(cursor.lastrowid)


def default_feedback_path() -> Path:
    return Path(__file__).resolve().parents[2] / "data" / "travel_feedback.sqlite3"