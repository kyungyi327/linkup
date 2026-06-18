"""
repositories/workout_history_repo.py
Workout_History 테이블 DAO. 세션 내 동작별 1행.
"""

from pathlib import Path

from linkup.db.constants import BodyPart, SessionStatus
from linkup.db.models import WorkoutHistory

from ._mapper import enum_csv, row_to_history
from .db import get_connection


class WorkoutHistoryRepo:
    def __init__(self, db_path: Path | None = None) -> None:
        self._db_path = db_path

    def create(self, history: WorkoutHistory) -> int:
        """동작 기록 1건 삽입. is_completed 는 status 와 동기화."""
        is_completed = 1 if history.status == SessionStatus.COMPLETED else 0
        with get_connection(self._db_path) as conn:
            cur = conn.execute(
                """
                INSERT INTO Workout_History
                    (session_id, ex_id, seq_order, actual_sets, actual_duration_sec,
                     is_completed, used_modified, feedback, pain_during, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    history.session_id,
                    history.ex_id,
                    history.seq_order,
                    history.actual_sets,
                    history.actual_duration_sec,
                    is_completed,
                    1 if history.used_modified else 0,
                    history.feedback,
                    enum_csv(history.pain_during),
                    history.status.value,
                ),
            )
            conn.commit()
            assert cur.lastrowid is not None  # INSERT 직후라 항상 존재
            return cur.lastrowid

    def update_status(
        self,
        history_id: int,
        status: SessionStatus,
        feedback: int | None = None,
        pain_during: list[BodyPart] | None = None,
        actual_sets: int | None = None,
        actual_duration_sec: int | None = None,
        used_modified: bool | None = None,
    ) -> None:
        """동작 상태 갱신. None 인 인자는 기존 값 유지."""
        sets_clauses = ["status = :status", "is_completed = :is_completed"]
        params: dict[str, object] = {
            "history_id": history_id,
            "status": status.value,
            "is_completed": 1 if status == SessionStatus.COMPLETED else 0,
        }
        if feedback is not None:
            sets_clauses.append("feedback = :feedback")
            params["feedback"] = feedback
        if pain_during is not None:
            sets_clauses.append("pain_during = :pain_during")
            params["pain_during"] = enum_csv(pain_during)
        if actual_sets is not None:
            sets_clauses.append("actual_sets = :actual_sets")
            params["actual_sets"] = actual_sets
        if actual_duration_sec is not None:
            sets_clauses.append("actual_duration_sec = :actual_duration_sec")
            params["actual_duration_sec"] = actual_duration_sec
        if used_modified is not None:
            sets_clauses.append("used_modified = :used_modified")
            params["used_modified"] = 1 if used_modified else 0

        sql = "UPDATE Workout_History SET " + ", ".join(sets_clauses) + " WHERE history_id = :history_id"
        with get_connection(self._db_path) as conn:
            conn.execute(sql, params)
            conn.commit()

    def list_by_session(self, session_id: int) -> list[WorkoutHistory]:
        with get_connection(self._db_path) as conn:
            rows = conn.execute(
                """
                SELECT * FROM Workout_History
                 WHERE session_id = ?
                 ORDER BY seq_order
                """,
                (session_id,),
            ).fetchall()
        return [row_to_history(r) for r in rows]
