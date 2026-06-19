from __future__ import annotations

from typing import TYPE_CHECKING

from linkup.db.provider import SqliteDataProvider
from linkup.ui.port import DailyLog, Routine, UserProfile

if TYPE_CHECKING:
    from pathlib import Path

    from tests.db.conftest import InsertExercise


def test_sqlite_data_provider_smoke_profile_log_and_session_flow(
    initialized_db: Path,
    insert_exercise: InsertExercise,
) -> None:
    insert_exercise("EX_001", name="목 스트레칭", target_muscle=["neck"], duration_sec=60)
    insert_exercise("EX_002", name="어깨 스트레칭", target_muscle=["shoulders"], duration_sec=90)
    provider = SqliteDataProvider(initialized_db, auto_init=False)

    provider.save_user_profile(
        UserProfile(
            nickname="테스터",
            birth_year=1995,
            gender="female",
            pain_points=["neck"],
            pushup_max=12,
            plank_max_sec=60,
            squat_max=20,
            height_cm=165,
            weight_kg=55,
        )
    )
    provider.upsert_today_log(
        DailyLog(
            mental_condition_score=7,
            outdoor_hours=2.0,
            fatigue_by_part={"shoulder": 4},
        )
    )

    profile = provider.get_user_profile()
    log = provider.get_today_log()
    routine = provider.generate_routine(3)
    session_id = provider.start_session(Routine(items=routine.items[:2], expected_minutes=3))
    provider.record_history(session_id, "EX_001", completed=True)
    provider.record_history(session_id, "EX_002", completed=False)
    summary = provider.end_session(session_id, "적당해요", "없어요", "메모")

    assert provider.has_user_profile()
    assert profile.nickname == "테스터"
    assert profile.gender == "female"
    assert profile.pain_points == ["neck"]
    assert log is not None
    assert log.mental_condition_score == 7
    assert log.fatigue_by_part == {"shoulder": 4}
    assert [item.ex_id for item in routine.items] == ["EX_001", "EX_002"]
    assert summary.completed_count == 1
    assert summary.duration_min >= 0
