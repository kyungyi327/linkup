from __future__ import annotations

import sqlite3
from datetime import date, timedelta
from typing import TYPE_CHECKING

import pytest

from linkup.db.constants import (
    BodyPart,
    ExerciseCategory,
    Gender,
    Goal,
    JobType,
    Scene,
    SessionStatus,
)
from linkup.db.models import DailyLog, UserProfile, WorkoutHistory
from linkup.db.repositories import (
    AppSettingsRepo,
    DailyLogRepo,
    ExerciseLibraryRepo,
    StatsRepo,
    UserProfileRepo,
    WorkoutHistoryRepo,
    WorkoutSessionRepo,
    get_connection,
)

if TYPE_CHECKING:
    from pathlib import Path

    from tests.db.conftest import InsertExercise


def test_user_profile_repo_round_trips_enums_lists_nullable_fields_and_booleans(initialized_db: Path) -> None:
    repo = UserProfileRepo(initialized_db)

    assert not repo.has_profile()

    repo.save(
        UserProfile(
            nickname="테스터",
            gender=Gender.FEMALE,
            birth_year=1995,
            height_cm=165.5,
            weight_kg=55.25,
            job_type=JobType.IT,
            goals=[Goal.DIET, Goal.BASIC_FITNESS],
            pain_points=[BodyPart.NECK, BodyPart.SHOULDER],
            pushup_max=None,
            plank_max_sec=90,
            squat_max=30,
            notification_enabled=False,
        )
    )

    saved = repo.get()

    assert repo.has_profile()
    assert saved is not None
    assert saved.nickname == "테스터"
    assert saved.gender == Gender.FEMALE
    assert saved.job_type == JobType.IT
    assert saved.goals == [Goal.DIET, Goal.BASIC_FITNESS]
    assert saved.pain_points == [BodyPart.NECK, BodyPart.SHOULDER]
    assert saved.pushup_max is None
    assert saved.plank_max_sec == 90
    assert saved.squat_max == 30
    assert saved.notification_enabled is False


def test_daily_log_repo_round_trips_json_fatigue_by_part(initialized_db: Path) -> None:
    repo = DailyLogRepo(initialized_db)
    log = DailyLog(
        date="2026-01-02",
        mental_condition_score=8,
        outdoor_hours=1.5,
        fatigue_by_part={BodyPart.NECK: 7, BodyPart.WRIST: 3},
        manual_scene=Scene.HOME,
    )

    repo.upsert(log)
    saved = repo.get("2026-01-02")

    assert saved is not None
    assert saved.mental_condition_score == 8
    assert saved.outdoor_hours == 1.5
    assert saved.fatigue_by_part == {BodyPart.NECK: 7, BodyPart.WRIST: 3}
    assert saved.manual_scene == Scene.HOME


def test_app_settings_repo_reads_defaults_and_updates_values(initialized_db: Path) -> None:
    repo = AppSettingsRepo(initialized_db)

    assert repo.db_version() == "2"
    assert not repo.is_onboarding_completed()

    repo.mark_onboarding_completed()
    repo.set("theme", "dark")

    assert repo.is_onboarding_completed()
    assert repo.get("theme") == "dark"


def test_exercise_library_repo_filters_and_loads_modified_exercise(
    initialized_db: Path,
    insert_exercise: InsertExercise,
) -> None:
    insert_exercise("EX_EASY", name="쉬운 운동", difficulty_level=1)
    insert_exercise("EX_HARD", difficulty_level=3)
    insert_exercise("EX_HOME", suitable_scenes=[Scene.HOME])
    insert_exercise("EX_SHOULDER", contraindications=[BodyPart.SHOULDER])
    insert_exercise("EX_ORIGINAL", modified_ex_id="EX_EASY")
    repo = ExerciseLibraryRepo(initialized_db)

    rows = repo.query(
        category=ExerciseCategory.STRETCH,
        scene=Scene.OFFICE,
        max_difficulty=2,
        avoid_body_parts=[BodyPart.SHOULDER],
    )
    modified = repo.get_modified("EX_ORIGINAL")

    assert [row.ex_id for row in rows] == ["EX_EASY", "EX_ORIGINAL"]
    assert modified is not None
    assert modified.ex_id == "EX_EASY"
    assert modified.name == "쉬운 운동"


def test_workout_session_requires_daily_log_and_calculates_duration(initialized_db: Path) -> None:
    repo = WorkoutSessionRepo(initialized_db)
    log_repo = DailyLogRepo(initialized_db)

    with pytest.raises(sqlite3.IntegrityError, match="Daily_Log record must exist"):
        repo.start("2026-01-02", Scene.OFFICE, "10:00:00")

    log_repo.upsert(DailyLog(date="2026-01-02"))
    session_id = repo.start("2026-01-02", Scene.OFFICE, "10:00:00")
    repo.end(session_id, "10:07:30", overall_feedback=1, memo="완료")
    saved = repo.get(session_id)

    assert saved is not None
    assert saved.scene == Scene.OFFICE
    assert saved.total_duration_sec == 450
    assert saved.overall_feedback == 1
    assert saved.memo == "완료"
    assert saved.is_completed is True


def test_workout_history_status_update_syncs_completion_flag(
    initialized_db: Path,
    insert_exercise: InsertExercise,
) -> None:
    insert_exercise("EX_001")
    DailyLogRepo(initialized_db).upsert(DailyLog(date="2026-01-02"))
    session_id = WorkoutSessionRepo(initialized_db).start("2026-01-02", None, "10:00:00")
    repo = WorkoutHistoryRepo(initialized_db)
    history_id = repo.create(
        WorkoutHistory(
            session_id=session_id,
            ex_id="EX_001",
            seq_order=1,
            status=SessionStatus.PENDING,
        )
    )

    repo.update_status(
        history_id,
        SessionStatus.COMPLETED,
        feedback=1,
        pain_during=[BodyPart.WRIST],
        actual_sets=2,
        actual_duration_sec=60,
        used_modified=True,
    )
    completed = repo.list_by_session(session_id)[0]
    repo.update_status(history_id, SessionStatus.SKIPPED)
    skipped = repo.list_by_session(session_id)[0]

    assert completed.status == SessionStatus.COMPLETED
    assert completed.is_completed is True
    assert completed.feedback == 1
    assert completed.pain_during == [BodyPart.WRIST]
    assert completed.actual_sets == 2
    assert completed.actual_duration_sec == 60
    assert completed.used_modified is True
    assert skipped.status == SessionStatus.SKIPPED
    assert skipped.is_completed is False


def test_stats_repo_calculates_streak_totals_and_daily_history(initialized_db: Path) -> None:
    log_repo = DailyLogRepo(initialized_db)
    session_repo = WorkoutSessionRepo(initialized_db)
    stats_repo = StatsRepo(initialized_db)
    today = date.today()
    yesterday = today - timedelta(days=1)

    for day, started_at, ended_at in (
        (yesterday, "09:00:00", "09:04:00"),
        (today, "10:00:00", "10:05:00"),
        (today, "11:00:00", "11:03:00"),
    ):
        log_repo.upsert(DailyLog(date=day.isoformat()))
        session_id = session_repo.start(day.isoformat(), None, started_at)
        session_repo.end(session_id, ended_at)

    recent = stats_repo.recent_stats(7)
    history = stats_repo.daily_history(10)

    assert recent.active_days == 2
    assert recent.streak_days == 2
    assert recent.total_chunks == 3
    assert recent.total_minutes == 12
    assert stats_repo.daily_total_minutes(today.isoformat()) == 8
    assert [(row.date, row.total_minutes, row.chunk_count) for row in history[:2]] == [
        (today.isoformat(), 8, 2),
        (yesterday.isoformat(), 4, 1),
    ]
    assert [chunk.started_at for chunk in stats_repo.list_today_chunks(today.isoformat())] == [
        "10:00:00",
        "11:00:00",
    ]


def test_row_mappers_ignore_unknown_enum_tokens(initialized_db: Path) -> None:
    with get_connection(initialized_db) as conn:
        conn.execute(
            """
            UPDATE User_Profile
               SET goals = 'diet,unknown',
                   pain_points = 'neck,unknown',
                   nickname = '매퍼'
             WHERE id = 1
            """
        )
        conn.commit()

    saved = UserProfileRepo(initialized_db).get()

    assert saved is not None
    assert saved.goals == [Goal.DIET]
    assert saved.pain_points == [BodyPart.NECK]
