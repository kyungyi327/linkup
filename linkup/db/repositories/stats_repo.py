"""
repositories/stats_repo.py
Workout_Session / Daily_Log 집계 통계 DAO (읽기 전용).
"""

from dataclasses import dataclass
from typing import List

from linkup.db.models import WorkoutSession
from .db import get_connection
from ._mapper import row_to_session


@dataclass
class RecentStats:
    """Dashboard / History 요약.

    active_days   : 기간 내 운동한 날 수
    streak_days   : 오늘 기준 연속 운동 일수
    total_chunks  : 기간 내 총 chunk 수
    total_minutes : 기간 내 총 운동 분
    """
    active_days: int
    streak_days: int
    total_chunks: int
    total_minutes: int


@dataclass
class DailyHistorySummary:
    """History 화면 한 행 = 하루치."""
    date: str
    total_minutes: int
    chunk_count: int


class StatsRepo:

    def __init__(self, db_path=None):
        self._db_path = db_path

    def recent_stats(self, days: int = 7) -> RecentStats:
        """오늘 포함 최근 `days` 일 통계."""
        since = f"-{days - 1} days"
        with get_connection(self._db_path) as conn:
            row = conn.execute(
                """
                SELECT
                    COUNT(DISTINCT date)                AS active_days,
                    COUNT(*)                            AS total_chunks,
                    COALESCE(SUM(total_duration_sec), 0) AS total_sec
                FROM Workout_Session
                WHERE date >= date('now', 'localtime', ?)
                """,
                (since,),
            ).fetchone()
            active_days = row["active_days"]
            total_chunks = row["total_chunks"]
            total_minutes = row["total_sec"] // 60

            dates = [
                r["date"] for r in conn.execute(
                    "SELECT DISTINCT date FROM Workout_Session ORDER BY date DESC"
                ).fetchall()
            ]
        return RecentStats(
            active_days=active_days,
            streak_days=self._streak(dates),
            total_chunks=total_chunks,
            total_minutes=total_minutes,
        )

    @staticmethod
    def _streak(desc_dates: List[str]) -> int:
        """오늘(또는 어제)부터 연속된 운동 일수.

        desc_dates 는 'YYYY-MM-DD' 내림차순. 오늘/어제 둘 다 없으면 0.
        """
        from datetime import date as _date, timedelta
        have = set(desc_dates)
        today = _date.today()
        if today.isoformat() in have:
            cursor = today
        elif (today - timedelta(days=1)).isoformat() in have:
            cursor = today - timedelta(days=1)
        else:
            return 0
        streak = 0
        while cursor.isoformat() in have:
            streak += 1
            cursor -= timedelta(days=1)
        return streak

    def daily_history(self, limit: int = 50) -> List[DailyHistorySummary]:
        """최근 운동한 날들 (최신순), 일별 집계."""
        with get_connection(self._db_path) as conn:
            rows = conn.execute(
                """
                SELECT date,
                       COUNT(*)                            AS chunk_count,
                       COALESCE(SUM(total_duration_sec), 0) AS total_sec
                FROM Workout_Session
                GROUP BY date
                ORDER BY date DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [
            DailyHistorySummary(
                date=r["date"],
                total_minutes=r["total_sec"] // 60,
                chunk_count=r["chunk_count"],
            )
            for r in rows
        ]

    def daily_total_minutes(self, date: str) -> int:
        with get_connection(self._db_path) as conn:
            row = conn.execute(
                """
                SELECT COALESCE(SUM(total_duration_sec), 0) AS total_sec
                FROM Workout_Session
                WHERE date = ?
                """,
                (date,),
            ).fetchone()
        return row["total_sec"] // 60

    def list_today_chunks(self, date: str) -> List[WorkoutSession]:
        with get_connection(self._db_path) as conn:
            rows = conn.execute(
                """
                SELECT * FROM Workout_Session
                WHERE date = ?
                ORDER BY started_at
                """,
                (date,),
            ).fetchall()
        return [row_to_session(r) for r in rows]
