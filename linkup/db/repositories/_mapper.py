"""
repositories/_mapper.py
sqlite3.Row <-> dataclass 변환 헬퍼.

DB 는 CSV / JSON / enum 값을 TEXT 로 저장하고,
dataclass 는 List / Dict / Enum 으로 다룬다. 이 모듈이 그 사이를 변환한다.
"""

import json
from collections.abc import Iterable
from enum import Enum, StrEnum
from sqlite3 import Row

from linkup.db.constants import (
    BodyPart,
    ExerciseCategory,
    Gender,
    Goal,
    JobType,
    Scene,
    SessionStatus,
    join_csv,
    parse_csv,
)
from linkup.db.models import (
    DailyLog,
    ExerciseLibraryItem,
    UserProfile,
    WorkoutHistory,
    WorkoutSession,
)


# ------------------------------------------------------------------
# 작은 유틸
# ------------------------------------------------------------------
def _enum_or_none[T: Enum](enum_cls: type[T], value: str | None) -> T | None:
    """TEXT 값을 Enum 으로. value 가 None 이면 None."""
    return enum_cls(value) if value is not None else None


def _enum_list[T: Enum](enum_cls: type[T], csv: str | None) -> list[T]:
    """CSV TEXT 를 Enum 리스트로. 알 수 없는 토큰은 무시 (행 전체 로드 실패 방지)."""
    out: list[T] = []
    for v in parse_csv(csv or ""):
        try:
            out.append(enum_cls(v))
        except ValueError:
            pass
    return out


def enum_csv(items: Iterable[StrEnum | str]) -> str:
    """Enum 리스트를 CSV TEXT 로."""
    return join_csv([item.value if isinstance(item, Enum) else item for item in items])


def _to_bool(value: object) -> bool:
    return bool(value)


# ------------------------------------------------------------------
# User_Profile
# ------------------------------------------------------------------
def row_to_user_profile(r: Row) -> UserProfile:
    return UserProfile(
        id=r["id"],
        nickname=r["nickname"],
        avatar_path=r["avatar_path"],
        gender=_enum_or_none(Gender, r["gender"]),
        birth_year=r["birth_year"],
        height_cm=r["height_cm"],
        weight_kg=r["weight_kg"],
        job_type=JobType(r["job_type"]),
        goals=_enum_list(Goal, r["goals"]),
        goal_duration_weeks=r["goal_duration_weeks"],
        weekly_frequency=r["weekly_frequency"],
        pain_points=_enum_list(BodyPart, r["pain_points"]),
        pushup_max=r["pushup_max"],
        plank_max_sec=r["plank_max_sec"],
        squat_max=r["squat_max"],
        notification_enabled=_to_bool(r["notification_enabled"]),
        created_at=r["created_at"],
        updated_at=r["updated_at"],
    )


def user_profile_to_params(p: UserProfile) -> dict[str, object]:
    """save() 의 UPSERT 바인딩용 dict."""
    return {
        "id": p.id,
        "nickname": p.nickname,
        "avatar_path": p.avatar_path,
        "gender": p.gender.value if p.gender else None,
        "birth_year": p.birth_year,
        "height_cm": p.height_cm,
        "weight_kg": p.weight_kg,
        "job_type": p.job_type.value,
        "goals": enum_csv(p.goals),
        "goal_duration_weeks": p.goal_duration_weeks,
        "weekly_frequency": p.weekly_frequency,
        "pain_points": enum_csv(p.pain_points),
        "pushup_max": p.pushup_max,
        "plank_max_sec": p.plank_max_sec,
        "squat_max": p.squat_max,
        "notification_enabled": 1 if p.notification_enabled else 0,
    }


# ------------------------------------------------------------------
# Exercise_Library
# ------------------------------------------------------------------
def row_to_exercise(r: Row) -> ExerciseLibraryItem:
    return ExerciseLibraryItem(
        ex_id=r["ex_id"],
        name=r["name"],
        category=ExerciseCategory(r["category"]),
        target_muscle=parse_csv(r["target_muscle"] or ""),
        difficulty_level=r["difficulty_level"],
        contraindications=_enum_list(BodyPart, r["contraindications"]),
        modified_ex_id=r["modified_ex_id"],
        suitable_scenes=_enum_list(Scene, r["suitable_scenes"]),
        default_sets=r["default_sets"],
        default_reps=r["default_reps"],
        duration_sec=r["duration_sec"],
        description=r["description"],
        instruction_steps=r["instruction_steps"],
        media_path=r["media_path"],
    )


# ------------------------------------------------------------------
# Daily_Log
# ------------------------------------------------------------------
def row_to_daily_log(r: Row) -> DailyLog:
    raw = r["fatigue_by_part"] or "{}"
    parsed: dict[BodyPart, int] = {}
    for k, v in json.loads(raw).items():
        parsed[BodyPart(k)] = v
    return DailyLog(
        date=r["date"],
        mental_condition_score=r["mental_condition_score"],
        outdoor_hours=r["outdoor_hours"],
        fatigue_by_part=parsed,
        manual_scene=_enum_or_none(Scene, r["manual_scene"]),
        created_at=r["created_at"],
    )


def daily_log_to_params(log: DailyLog) -> dict[str, object]:
    fatigue = {
        (k.value if isinstance(k, BodyPart) else k): v
        for k, v in (log.fatigue_by_part or {}).items()
    }
    return {
        "date": log.date,
        "mental_condition_score": log.mental_condition_score,
        "outdoor_hours": log.outdoor_hours,
        "fatigue_by_part": json.dumps(fatigue, ensure_ascii=False),
        "manual_scene": log.manual_scene.value if log.manual_scene else None,
    }


# ------------------------------------------------------------------
# Workout_Session
# ------------------------------------------------------------------
def row_to_session(r: Row) -> WorkoutSession:
    return WorkoutSession(
        session_id=r["session_id"],
        date=r["date"],
        started_at=r["started_at"],
        ended_at=r["ended_at"],
        total_duration_sec=r["total_duration_sec"],
        scene=_enum_or_none(Scene, r["scene"]),
        overall_feedback=r["overall_feedback"],
        memo=r["memo"],
        is_completed=_to_bool(r["is_completed"]),
    )


# ------------------------------------------------------------------
# Workout_History
# ------------------------------------------------------------------
def row_to_history(r: Row) -> WorkoutHistory:
    return WorkoutHistory(
        history_id=r["history_id"],
        session_id=r["session_id"],
        ex_id=r["ex_id"],
        seq_order=r["seq_order"],
        actual_sets=r["actual_sets"],
        actual_duration_sec=r["actual_duration_sec"],
        is_completed=_to_bool(r["is_completed"]),
        used_modified=_to_bool(r["used_modified"]),
        feedback=r["feedback"],
        pain_during=_enum_list(BodyPart, r["pain_during"]),
        status=SessionStatus(r["status"]),
    )
