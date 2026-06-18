"""
repositories/daily_log_repo.py
Daily_Log 테이블 DAO. 하루 1행 (date PK).
"""

from pathlib import Path

from linkup.db.models import DailyLog

from ._mapper import daily_log_to_params, row_to_daily_log
from .db import get_connection


class DailyLogRepo:
    def __init__(self, db_path: Path | None = None) -> None:
        self._db_path = db_path

    def get(self, date: str) -> DailyLog | None:
        with get_connection(self._db_path) as conn:
            row = conn.execute(
                "SELECT * FROM Daily_Log WHERE date = ?", (date,)
            ).fetchone()
        return row_to_daily_log(row) if row else None

    def get_today(self) -> DailyLog | None:
        with get_connection(self._db_path) as conn:
            row = conn.execute(
                "SELECT * FROM Daily_Log WHERE date = date('now','localtime')"
            ).fetchone()
        return row_to_daily_log(row) if row else None

    def upsert(self, log: DailyLog) -> None:
        params = daily_log_to_params(log)
        with get_connection(self._db_path) as conn:
            conn.execute(
                """
                INSERT INTO Daily_Log
                    (date, mental_condition_score, outdoor_hours,
                     fatigue_by_part, manual_scene)
                VALUES
                    (:date, :mental_condition_score, :outdoor_hours,
                     :fatigue_by_part, :manual_scene)
                ON CONFLICT(date) DO UPDATE SET
                    mental_condition_score=:mental_condition_score,
                    outdoor_hours=:outdoor_hours,
                    fatigue_by_part=:fatigue_by_part,
                    manual_scene=:manual_scene
                """,
                params,
            )
            conn.commit()
