from __future__ import annotations

from abc import abstractmethod
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
    """외부 데이터 수집/저장 구현체가 제공해야 하는 사용자 입력 port."""

    @abstractmethod
    def has_user_profile(self) -> bool: ...

    @abstractmethod
    def get_user_profile(self) -> UserProfile: ...

    @abstractmethod
    def save_user_profile(self, profile: UserProfile) -> None: ...

    @abstractmethod
    def get_today_log(self) -> DailyLog | None: ...

    @abstractmethod
    def upsert_today_log(self, log: DailyLog) -> None: ...


class ExerciseContentPort(Protocol):
    """외부 운동 콘텐츠 구현체가 제공해야 하는 port."""

    @abstractmethod
    def get_modified_exercise(self, ex_id: str) -> Exercise: ...


class AnalysisPort(Protocol):
    """외부 분석/추천 구현체가 제공해야 하는 port."""

    @abstractmethod
    def generate_routine(self, available_min: int) -> Routine: ...

    @abstractmethod
    def get_recent_stats(self) -> RecentStats: ...

    @abstractmethod
    def get_session_list(self) -> list[SessionRecord]: ...


class SessionRecordPort(Protocol):
    """외부 운동 세션 기록 구현체가 제공해야 하는 port."""

    @abstractmethod
    def start_session(self, routine: Routine) -> str: ...

    @abstractmethod
    def record_history(self, session_id: str, ex_id: str, completed: bool) -> None: ...

    @abstractmethod
    def end_session(self, session_id: str, difficulty: str, pain: str, memo: str) -> SessionSummary: ...


class DataProvider(
    DataCollectionPort,
    ExerciseContentPort,
    AnalysisPort,
    SessionRecordPort,
    Protocol,
):
    """UI가 의존하는 전체 외부 provider 계약."""

    pass
