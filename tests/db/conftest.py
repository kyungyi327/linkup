from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

import pytest

from linkup.db.constants import BodyPart, ExerciseCategory, Scene
from linkup.db.repositories import get_connection, init_db

if TYPE_CHECKING:
    import sqlite3
    from collections.abc import Iterator
    from pathlib import Path


class InsertExercise(Protocol):
    def __call__(
        self,
        ex_id: str,
        *,
        name: str | None = None,
        category: ExerciseCategory = ExerciseCategory.STRETCH,
        target_muscle: list[str] | None = None,
        difficulty_level: int = 1,
        contraindications: list[BodyPart] | None = None,
        modified_ex_id: str | None = None,
        suitable_scenes: list[Scene] | None = None,
        default_sets: int = 1,
        default_reps: int = 1,
        duration_sec: int = 30,
        description: str | None = None,
    ) -> str: ...


def _csv(items: list[BodyPart | Scene | str]) -> str:
    return ",".join(item.value if isinstance(item, BodyPart | Scene) else item for item in items)


@pytest.fixture
def initialized_db(tmp_path: Path) -> Path:
    db_path = tmp_path / "linkup-test.db"
    init_db(db_path)
    return db_path


@pytest.fixture
def conn(initialized_db: Path) -> Iterator[sqlite3.Connection]:
    with get_connection(initialized_db) as connection:
        yield connection


@pytest.fixture
def insert_exercise(initialized_db: Path) -> InsertExercise:
    def _insert(
        ex_id: str,
        *,
        name: str | None = None,
        category: ExerciseCategory = ExerciseCategory.STRETCH,
        target_muscle: list[str] | None = None,
        difficulty_level: int = 1,
        contraindications: list[BodyPart] | None = None,
        modified_ex_id: str | None = None,
        suitable_scenes: list[Scene] | None = None,
        default_sets: int = 1,
        default_reps: int = 1,
        duration_sec: int = 30,
        description: str | None = None,
    ) -> str:
        with get_connection(initialized_db) as connection:
            connection.execute(
                """
                INSERT INTO Exercise_Library
                    (ex_id, name, category, target_muscle, difficulty_level,
                     contraindications, modified_ex_id, suitable_scenes,
                     default_sets, default_reps, duration_sec, description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    ex_id,
                    name or ex_id,
                    category.value,
                    _csv(target_muscle or ["neck"]),
                    difficulty_level,
                    _csv(contraindications or []),
                    modified_ex_id,
                    _csv(suitable_scenes or [Scene.OFFICE, Scene.HOME]),
                    default_sets,
                    default_reps,
                    duration_sec,
                    description,
                ),
            )
            connection.commit()
        return ex_id

    return _insert
