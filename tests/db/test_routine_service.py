from __future__ import annotations

from typing import TYPE_CHECKING

from linkup.db.constants import BodyPart, Gender
from linkup.db.models import DailyLog, UserProfile
from linkup.db.repositories import DailyLogRepo, UserProfileRepo
from linkup.db.services.routine_service import RoutineService

if TYPE_CHECKING:
    from pathlib import Path

    from tests.db.conftest import InsertExercise


def test_routine_service_avoids_profile_pain_and_high_fatigue_parts(
    initialized_db: Path,
    insert_exercise: InsertExercise,
) -> None:
    insert_exercise("EX_A_OK", difficulty_level=1)
    insert_exercise("EX_B_OK", difficulty_level=2)
    insert_exercise("EX_C_HARD", difficulty_level=3)
    insert_exercise("EX_D_NECK", contraindications=[BodyPart.NECK])
    insert_exercise("EX_E_WRIST", contraindications=[BodyPart.WRIST])
    UserProfileRepo(initialized_db).save(
        UserProfile(
            nickname="테스터",
            gender=Gender.MALE,
            pain_points=[BodyPart.NECK],
            pushup_max=20,
        )
    )
    DailyLogRepo(initialized_db).upsert(
        DailyLog(
            date="2026-01-02",
            fatigue_by_part={BodyPart.WRIST: 7, BodyPart.SHOULDER: 6},
        )
    )

    routine = RoutineService(initialized_db).generate("2026-01-02", available_min=3)

    assert [item.ex_id for item in routine] == ["EX_A_OK", "EX_B_OK"]


def test_routine_service_uses_pushup_count_for_max_difficulty(
    initialized_db: Path,
    insert_exercise: InsertExercise,
) -> None:
    insert_exercise("EX_A_EASY", difficulty_level=1)
    insert_exercise("EX_B_MEDIUM", difficulty_level=2)
    insert_exercise("EX_C_HARD", difficulty_level=3)
    profile_repo = UserProfileRepo(initialized_db)
    service = RoutineService(initialized_db)

    profile_repo.save(UserProfile(nickname="초급", pushup_max=5))
    assert [item.ex_id for item in service.generate("2026-01-02", 10)] == ["EX_A_EASY"]

    profile_repo.save(UserProfile(nickname="중급", pushup_max=20))
    assert [item.ex_id for item in service.generate("2026-01-02", 10)] == ["EX_A_EASY", "EX_B_MEDIUM"]

    profile_repo.save(UserProfile(nickname="상급", pushup_max=30))
    assert [item.ex_id for item in service.generate("2026-01-02", 10)] == [
        "EX_A_EASY",
        "EX_B_MEDIUM",
        "EX_C_HARD",
    ]
