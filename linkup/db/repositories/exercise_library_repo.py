"""
repositories/exercise_library_repo.py
Exercise_Library 테이블 DAO. 정적 동작 데이터.
"""

from pathlib import Path

from linkup.db.constants import BodyPart, ExerciseCategory, Scene
from linkup.db.models import ExerciseLibraryItem

from ._mapper import row_to_exercise
from .db import get_connection


class ExerciseLibraryRepo:
    def __init__(self, db_path: Path | None = None) -> None:
        self._db_path = db_path

    def get(self, ex_id: str) -> ExerciseLibraryItem | None:
        with get_connection(self._db_path) as conn:
            row = conn.execute("SELECT * FROM Exercise_Library WHERE ex_id = ?", (ex_id,)).fetchone()
        return row_to_exercise(row) if row else None

    def get_modified(self, ex_id: str) -> ExerciseLibraryItem | None:
        """난이도 하향 대체 동작 (modified_ex_id) 조회."""
        with get_connection(self._db_path) as conn:
            row = conn.execute(
                """
                SELECT m.* FROM Exercise_Library e
                  JOIN Exercise_Library m ON e.modified_ex_id = m.ex_id
                 WHERE e.ex_id = ?
                """,
                (ex_id,),
            ).fetchone()
        return row_to_exercise(row) if row else None

    def list_all(self) -> list[ExerciseLibraryItem]:
        with get_connection(self._db_path) as conn:
            rows = conn.execute("SELECT * FROM Exercise_Library ORDER BY ex_id").fetchall()
        return [row_to_exercise(r) for r in rows]

    def query(
        self,
        category: ExerciseCategory | None = None,
        scene: Scene | None = None,
        max_difficulty: int | None = None,
        avoid_body_parts: list[BodyPart] | None = None,
    ) -> list[ExerciseLibraryItem]:
        """routine 알고리즘용 필터. 통증 부위 회피는 Python 단에서 처리."""
        clauses: list[str] = []
        params: list[str] = []
        if category is not None:
            clauses.append("category = ?")
            params.append(category.value)
        if scene is not None:
            clauses.append("(suitable_scenes LIKE ?)")
            params.append(f"%{scene.value}%")
        if max_difficulty is not None:
            clauses.append("difficulty_level <= ?")
            params.append(f"{max_difficulty}")

        sql = "SELECT * FROM Exercise_Library"
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY ex_id"

        with get_connection(self._db_path) as conn:
            rows = conn.execute(sql, params).fetchall()
        items = [row_to_exercise(r) for r in rows]

        if avoid_body_parts:
            avoid = set(avoid_body_parts)
            items = [it for it in items if avoid.isdisjoint(set(it.contraindications))]
        return items
