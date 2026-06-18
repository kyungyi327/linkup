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

See docs/CHANGELOG_KOR.md for change history.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict

from linkup.db.constants import (
    BodyPart,
    ExerciseCategory,
    Scene,
    JobType,
    Gender,
    Goal,
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
    nickname: Optional[str] = None
    avatar_path: Optional[str] = None

    # Demographics
    gender: Optional[Gender] = None      # UI: 남/여
    birth_year: Optional[int] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    job_type: JobType = JobType.STUDENT  # INPUT.md 2-1

    # Goals / schedule
    goals: List[Goal] = field(default_factory=list)              # INPUT.md 2-2 (CSV in DB)
    goal_duration_weeks: Optional[int] = None                    # INPUT.md 2-3, 1~24
    weekly_frequency: Optional[int] = None                       # INPUT.md 2-4, 1~7

    # Pain points
    pain_points: List[BodyPart] = field(default_factory=list)    # INPUT.md 2-6 (CSV in DB)

    # Fitness benchmarks (INPUT.md 2-7)
    # NULL means "잘 모르겠다 (I don't know)"
    pushup_max: Optional[int] = None
    plank_max_sec: Optional[int] = None
    squat_max: Optional[int] = None

    # Misc
    notification_enabled: bool = True                            # INPUT.md 2-9

    # Timestamps (TEXT 'YYYY-MM-DD HH:MM:SS' in DB)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


# ------------------------------------------------------------------
# 2. Exercise_Library
#    Static seed data shipped with the application
#    (may later be augmented from external library).
# ------------------------------------------------------------------
@dataclass
class ExerciseLibraryItem:
    ex_id: str                                              # e.g. 'EX_001' or external slug
    name: str
    category: ExerciseCategory = ExerciseCategory.STRETCH
    target_muscle: List[str] = field(default_factory=list)  # CSV in DB
    difficulty_level: int = 1                                # 1~3
    contraindications: List[BodyPart] = field(default_factory=list)  # CSV in DB
    modified_ex_id: Optional[str] = None                     # self-ref FK (easier version)
    suitable_scenes: List[Scene] = field(default_factory=list)       # CSV in DB
    default_sets: int = 1
    default_reps: int = 1
    duration_sec: int = 30
    description: Optional[str] = None
    instruction_steps: Optional[str] = None                  # JSON array as TEXT
    media_path: Optional[str] = None


# ------------------------------------------------------------------
# 3. Daily_Log
#    One row per calendar day.
# ------------------------------------------------------------------
@dataclass
class DailyLog:
    date: str                                                # 'YYYY-MM-DD' (PK)

    # Unified mental condition score (team meeting decision)
    # 0~10, 10 = best. Replaces sleep_hours + mood_score + stress_score.
    mental_condition_score: Optional[int] = None

    # Outdoor activity time 0~16 hours (INPUT.md 3-2-1)
    outdoor_hours: Optional[float] = None

    # Per-body-part fatigue (INPUT.md 3-2-2)
    # Sparse dict — only parts with reported pain are included.
    # Stored as JSON TEXT in DB.
    fatigue_by_part: Dict[BodyPart, int] = field(default_factory=dict)

    manual_scene: Optional[Scene] = None
    created_at: Optional[str] = None


# ------------------------------------------------------------------
# 4. Workout_Session
#    One row per chunk (3~10 분 단위, 하루 누적).
# ------------------------------------------------------------------
@dataclass
class WorkoutSession:
    session_id: Optional[int] = None                         # AUTOINCREMENT
    date: str = ""                                            # FK → Daily_Log.date
    started_at: str = ""                                      # 'HH:MM:SS'
    ended_at: Optional[str] = None
    total_duration_sec: Optional[int] = None                  # Auto-computed by trigger
    scene: Optional[Scene] = None
    overall_feedback: Optional[int] = None                    # -1 / 0 / 1
    memo: Optional[str] = None                                # UI: 세션 완료 화면 메모(선택)
    is_completed: bool = False


# ------------------------------------------------------------------
# 5. Workout_History
#    Per-exercise record inside a chunk (Workout_Session).
# ------------------------------------------------------------------
@dataclass
class WorkoutHistory:
    history_id: Optional[int] = None                         # AUTOINCREMENT
    session_id: int = 0                                       # FK → Workout_Session
    ex_id: str = ""                                           # FK → Exercise_Library
    seq_order: int = 1                                        # 1, 2, 3, ... within the chunk
    actual_sets: Optional[int] = None
    actual_duration_sec: Optional[int] = None
    is_completed: bool = False                                # Kept for back-compat with status
    used_modified: bool = False                               # User switched to easier version mid-way
    feedback: Optional[int] = None                            # -1 / 0 / 1
    pain_during: List[BodyPart] = field(default_factory=list) # CSV in DB
    status: SessionStatus = SessionStatus.PENDING             # INPUT.md 5


# ------------------------------------------------------------------
# 6. App_Settings  (Key-Value store)
# ------------------------------------------------------------------
@dataclass
class AppSetting:
    key: str
    value: str
