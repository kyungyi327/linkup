from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class UserProfile:
    nickname: str
    birth_year: int | None
    gender: str | None
    pain_points: list[str]
    pushup_max: int | None
    plank_max_sec: int | None
    squat_max: int | None
    height_cm: int | None
    weight_kg: int | None


@dataclass(frozen=True)
class DailyLog:
    mental_condition_score: int | None
    outdoor_hours: float | None
    fatigue_by_part: dict[str, int]


@dataclass(frozen=True)
class Exercise:
    ex_id: str
    name: str
    target_muscle: str
    duration_text: str
    intensity: str
    guide: str
    modified_ex_id: str | None = None


@dataclass(frozen=True)
class Routine:
    items: list[Exercise]
    expected_minutes: int


@dataclass(frozen=True)
class RecentStats:
    streak_days: int
    workout_days_7d: int
    total_sessions: int
    total_hours: float


@dataclass(frozen=True)
class SessionSummary:
    duration_min: int
    completed_count: int
    streak_days: int


@dataclass(frozen=True)
class SessionRecord:
    date: str
    exercise_count: int
    duration_min: int
    difficulty_feedback: str
    pain_feedback: str
    memo: str


class DataCollectionPort(Protocol):
    def has_user_profile(self) -> bool: ...

    def get_user_profile(self) -> UserProfile: ...

    def save_user_profile(self, profile: UserProfile) -> None: ...

    def get_today_log(self) -> DailyLog | None: ...

    def upsert_today_log(self, log: DailyLog) -> None: ...


class ExerciseContentPort(Protocol):
    def get_modified_exercise(self, ex_id: str) -> Exercise: ...


class AnalysisPort(Protocol):
    def generate_routine(self, available_min: int) -> Routine: ...

    def get_recent_stats(self) -> RecentStats: ...

    def get_session_list(self) -> list[SessionRecord]: ...


class SessionRecordPort(Protocol):
    def start_session(self, routine: Routine) -> str: ...

    def record_history(self, session_id: str, ex_id: str, completed: bool) -> None: ...

    def end_session(
        self, session_id: str, difficulty: str, pain: str, memo: str
    ) -> SessionSummary: ...


class DataProvider(
    DataCollectionPort,
    ExerciseContentPort,
    AnalysisPort,
    SessionRecordPort,
    Protocol,
):
    pass
