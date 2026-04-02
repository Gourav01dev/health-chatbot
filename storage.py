from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional


@dataclass(frozen=True)
class Meal:
    id: int
    user_id: int
    text: str
    log_date: str
    created_at: str
    updated_at: Optional[str]


class Storage:
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def _connect(self) -> Iterable[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        try:
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA synchronous=NORMAL;")
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS meals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    log_date TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT
                );
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_meals_user_date ON meals(user_id, log_date);"
            )

    @staticmethod
    def _now_iso() -> str:
        return datetime.now().isoformat(timespec="seconds")

    def add_meal(self, user_id: int, text: str, log_date: str) -> Meal:
        created_at = self._now_iso()
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO meals(user_id, text, log_date, created_at) VALUES (?, ?, ?, ?)",
                (user_id, text, log_date, created_at),
            )
            meal_id = int(cur.lastrowid)
        return Meal(
            id=meal_id,
            user_id=user_id,
            text=text,
            log_date=log_date,
            created_at=created_at,
            updated_at=None,
        )

    def list_meals_for_day(self, user_id: int, log_date: str) -> list[Meal]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM meals WHERE user_id = ? AND log_date = ? ORDER BY id",
                (user_id, log_date),
            ).fetchall()
        return [self._row_to_meal(row) for row in rows]

    def get_meal(self, user_id: int, meal_id: int) -> Optional[Meal]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM meals WHERE user_id = ? AND id = ?",
                (user_id, meal_id),
            ).fetchone()
        return self._row_to_meal(row) if row else None

    def update_meal(self, user_id: int, meal_id: int, new_text: str) -> bool:
        updated_at = self._now_iso()
        with self._connect() as conn:
            cur = conn.execute(
                """
                UPDATE meals
                SET text = ?, updated_at = ?
                WHERE user_id = ? AND id = ?
                """,
                (new_text, updated_at, user_id, meal_id),
            )
            return cur.rowcount > 0

    def delete_meal(self, user_id: int, meal_id: int) -> bool:
        with self._connect() as conn:
            cur = conn.execute(
                "DELETE FROM meals WHERE user_id = ? AND id = ?",
                (user_id, meal_id),
            )
            return cur.rowcount > 0

    @staticmethod
    def _row_to_meal(row: sqlite3.Row) -> Meal:
        return Meal(
            id=row["id"],
            user_id=row["user_id"],
            text=row["text"],
            log_date=row["log_date"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
