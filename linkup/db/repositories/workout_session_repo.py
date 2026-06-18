"""
repositories/workout_session_repo.py
Workout_Session 테이블 DAO. chunk 1개 = 1행.
"""

from typing import Optional, List

from linkup.db.models import WorkoutSession
from linkup.db.constants import Scene
from .db import get_connection
from ._mapper import row_to_session


class WorkoutSessionRepo:

    def __init__(self, db_path=None):
        self._db_path = db_path

    def start(self, date: str, scene: Optional[Scene], started_at: str) -> int:
        """세션 시작. 해당 date 의 Daily_Log 가 먼저 있어야 함 (TRG-3)."""
        scene_val = scene.value if scene else None
        with get_connection(self._db_path) as conn:
            cur = conn.execute(
                """
                INSERT INTO Workout_Session (date, started_at, scene)
                VALUES (?, ?, ?)
                """,
                (date, started_at, scene_val),
            )
            conn.commit()
            assert cur.lastrowid is not None  # INSERT 직후라 항상 존재
            return cur.lastrowid

    def end(self,
            session_id: int,
            ended_at: str,
            overall_feedback: Optional[int] = None,
            is_completed: bool = True,
            memo: Optional[str] = None) -> None:
        """세션 종료. ended_at 설정 시 트리거가 total_duration_sec 계산."""
        with get_connection(self._db_path) as conn:
            conn.execute(
                """
                UPDATE Workout_Session
                   SET ended_at = ?, overall_feedback = ?,
                       is_completed = ?, memo = ?
                 WHERE session_id = ?
                """,
                (ended_at, overall_feedback, 1 if is_completed else 0,
                 memo, session_id),
            )
            conn.commit()

    def get(self, session_id: int) -> Optional[WorkoutSession]:
        with get_connection(self._db_path) as conn:
            row = conn.execute(
                "SELECT * FROM Workout_Session WHERE session_id = ?",
                (session_id,),
            ).fetchone()
        return row_to_session(row) if row else None

    def list_by_date(self, date: str) -> List[WorkoutSession]:
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
