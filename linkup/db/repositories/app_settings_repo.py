"""
repositories/app_settings_repo.py
App_Settings key-value 테이블 DAO.
"""

from pathlib import Path

from .db import get_connection


class AppSettingsRepo:
    def __init__(self, db_path: Path | None = None) -> None:
        self._db_path = db_path

    def get(self, key: str) -> str | None:
        with get_connection(self._db_path) as conn:
            row = conn.execute(
                "SELECT value FROM App_Settings WHERE key = ?", (key,)
            ).fetchone()
        return row["value"] if row else None

    def set(self, key: str, value: str) -> None:
        with get_connection(self._db_path) as conn:
            conn.execute(
                """
                INSERT INTO App_Settings (key, value) VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                (key, value),
            )
            conn.commit()

    def is_onboarding_completed(self) -> bool:
        return self.get("onboarding_completed") == "true"

    def mark_onboarding_completed(self) -> None:
        self.set("onboarding_completed", "true")

    def db_version(self) -> str:
        return self.get("db_version") or "1"
