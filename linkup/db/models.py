"""
models.py
Team LinkUp — Dataclass definitions for all 6 tables.

These are pure data containers. They know nothing about SQL.
The DAO layer (repositories/) converts between dataclass instances
and SQLite rows.

Naming convention:
    Table `User_Profile` ↔ class `UserProfile`
    Table `Daily_Log`    ↔ class `DailyLog`
    etc.

CSV / JSON fields are represented as Python lists / dicts here;
DAO is responsible for serializing them to TEXT on save.
"""

from dataclasses import dataclass, field

from linkup.db.constants import (
    BodyPart,
    ExerciseCategory,
    Gender,
    Goal,
    JobType,
    Scene,
    SessionStatus,
)


# ------------------------------------------------------------------
# 1. User_Profile
#    Local single-user app: always one row (id = 1).
# ------------------------------------------------------------------
@dataclass
class UserProfile:
    # Identity
    id: int = 1
    nickname: str | None = None
    avatar_path: str | None = None

    # Demographics
    gender: Gender | None = None  # UI: 남/여
    birth_year: int | None = None
    height_cm: float | None = None
    weight_kg: float | None = None
    job_type: JobType = JobType.STUDENT  # INPUT.md 2-1

    # Goals / schedule
    goals: list[Goal] = field(default_factory=list)  # INPUT.md 2-2 (CSV in DB)
    goal_duration_weeks: int | None = None  # INPUT.md 2-3, 1~24
    weekly_frequency: int | None = None  # INPUT.md 2-4, 1~7

    # Pain points
    pain_points: list[BodyPart] = field(default_factory=list)  # INPUT.md 2-6 (CSV in DB)

    # Fitness benchmarks (INPUT.md 2-7)
    # NULL means "잘 모르겠다 (I don't know)"
    pushup_max: int | None = None
    plank_max_sec: int | None = None
    squat_max: int | None = None

    # Misc
    notification_enabled: bool = True  # INPUT.md 2-9

    # Timestamps (TEXT 'YYYY-MM-DD HH:MM:SS' in DB)
    created_at: str | None = None
    updated_at: str | None = None


# ------------------------------------------------------------------
# 2. Exercise_Library
#    Static seed data shipped with the application
#    (may later be augmented from external library).
# ------------------------------------------------------------------
@dataclass
class ExerciseLibraryItem:
    ex_id: str  # e.g. 'EX_001' or external slug
    name: str
    category: ExerciseCategory = ExerciseCategory.STRETCH
    target_muscle: list[str] = field(default_factory=list)  # CSV in DB
    difficulty_level: int = 1  # 1~3
    contraindications: list[BodyPart] = field(default_factory=list)  # CSV in DB
    modified_ex_id: str | None = None  # self-ref FK (easier version)
    suitable_scenes: list[Scene] = field(default_factory=list)  # CSV in DB
    default_sets: int = 1
    default_reps: int = 1
    duration_sec: int = 30
    description: str | None = None
    instruction_steps: str | None = None  # JSON array as TEXT
    media_path: str | None = None


# ------------------------------------------------------------------
# 3. Daily_Log
#    One row per calendar day.
# ------------------------------------------------------------------
@dataclass
class DailyLog:
    date: str  # 'YYYY-MM-DD' (PK)

    # Unified mental condition score (team meeting decision)
    # 0~10, 10 = best. Replaces sleep_hours + mood_score + stress_score.
    mental_condition_score: int | None = None

    # Outdoor activity time 0~16 hours (INPUT.md 3-2-1)
    outdoor_hours: float | None = None

    # Per-body-part fatigue (INPUT.md 3-2-2)
    # Sparse dict — only parts with reported pain are included.
    # Stored as JSON TEXT in DB.
    fatigue_by_part: dict[BodyPart, int] = field(default_factory=dict)

    manual_scene: Scene | None = None
    created_at: str | None = None


# ------------------------------------------------------------------
# 4. Workout_Session
#    One row per chunk (3~10 분 단위, 하루 누적).
# ------------------------------------------------------------------
@dataclass
class WorkoutSession:
    session_id: int | None = None  # AUTOINCREMENT
    date: str = ""  # FK → Daily_Log.date
    started_at: str = ""  # 'HH:MM:SS'
    ended_at: str | None = None
    total_duration_sec: int | None = None  # Auto-computed by trigger
    scene: Scene | None = None
    overall_feedback: int | None = None  # -1 / 0 / 1
    memo: str | None = None  # UI: 세션 완료 화면 메모(선택)
    is_completed: bool = False


# ------------------------------------------------------------------
# 5. Workout_History
#    Per-exercise record inside a chunk (Workout_Session).
# ------------------------------------------------------------------
@dataclass
class WorkoutHistory:
    history_id: int | None = None  # AUTOINCREMENT
    session_id: int = 0  # FK → Workout_Session
    ex_id: str = ""  # FK → Exercise_Library
    seq_order: int = 1  # 1, 2, 3, ... within the chunk
    actual_sets: int | None = None
    actual_duration_sec: int | None = None
    is_completed: bool = False  # Kept for back-compat with status
    used_modified: bool = False  # User switched to easier version mid-way
    feedback: int | None = None  # -1 / 0 / 1
    pain_during: list[BodyPart] = field(default_factory=list)  # CSV in DB
    status: SessionStatus = SessionStatus.PENDING  # INPUT.md 5


# ------------------------------------------------------------------
# 6. App_Settings  (Key-Value store)
# ------------------------------------------------------------------
@dataclass
class AppSetting:
    key: str
    value: str
