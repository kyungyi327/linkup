from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from linkup.ui.port import Exercise, Routine


@dataclass(frozen=True)
class OnboardingState:
    screen_key: ClassVar[str] = "onboarding"

    def profile_saved(self) -> DashboardState:
        return DashboardState()


@dataclass(frozen=True)
class DashboardState:
    screen_key: ClassVar[str] = "dashboard"

    def open_condition(self) -> DailyLogState:
        return DailyLogState()

    def open_history(self) -> HistoryState:
        return HistoryState()

    def open_profile(self) -> ProfileEditState:
        return ProfileEditState()

    def start_routine_loading(
        self,
        available_min: int,
        message: str = "오늘 컨디션에 맞는 루틴을 준비하고 있어요",
    ) -> RoutineLoadingState:
        return RoutineLoadingState(
            available_min=max(3, min(10, available_min)),
            message=message,
        )


@dataclass(frozen=True)
class DailyLogState:
    screen_key: ClassVar[str] = "daily_log"

    def condition_done(self) -> DashboardState:
        return DashboardState()


@dataclass(frozen=True)
class RoutineLoadingState:
    available_min: int = 10
    message: str = "오늘 컨디션에 맞는 루틴을 준비하고 있어요"
    screen_key: ClassVar[str] = "routine_loading"

    def routine_loaded(self, routine: Routine) -> RoutinePreviewState:
        return RoutinePreviewState(routine=routine)


@dataclass(frozen=True)
class RoutinePreviewState:
    routine: Routine
    screen_key: ClassVar[str] = "routine_preview"

    def back(self) -> DashboardState:
        return DashboardState()

    def start_session(self, session_id: str) -> ExerciseExecutionState:
        return ExerciseExecutionState(routine=self.routine, session_id=session_id)


@dataclass(frozen=True)
class ExerciseExecutionState:
    routine: Routine
    session_id: str
    exercise_index: int = 0
    modified_exercise: Exercise | None = None
    screen_key: ClassVar[str] = "exercise"

    def current_exercise(self) -> Exercise:
        return self.routine.items[self.exercise_index]

    def exercise_modified(self, exercise: Exercise) -> ExerciseExecutionState:
        return replace(self, modified_exercise=exercise)

    def exercise_completed(self) -> ExerciseExecutionState | SessionCompleteState:
        if self.exercise_index >= len(self.routine.items) - 1:
            return SessionCompleteState(
                routine=self.routine,
                session_id=self.session_id,
            )

        return replace(
            self,
            exercise_index=self.exercise_index + 1,
            modified_exercise=None,
        )


@dataclass(frozen=True)
class SessionCompleteState:
    routine: Routine
    session_id: str
    screen_key: ClassVar[str] = "complete"

    def finish(self) -> DashboardState:
        return DashboardState()

    def home(self) -> DashboardState:
        return DashboardState()


@dataclass(frozen=True)
class ProfileEditState:
    screen_key: ClassVar[str] = "profile_edit"

    def profile_saved(self) -> DashboardState:
        return DashboardState()

    def cancel(self) -> DashboardState:
        return DashboardState()


@dataclass(frozen=True)
class HistoryState:
    screen_key: ClassVar[str] = "history"

    def back(self) -> DashboardState:
        return DashboardState()


type AppState = (
    OnboardingState
    | DashboardState
    | DailyLogState
    | RoutineLoadingState
    | RoutinePreviewState
    | ExerciseExecutionState
    | SessionCompleteState
    | ProfileEditState
    | HistoryState
)


class AppStateMachine:
    def __init__(self, *, has_profile: bool) -> None:
        self.state: AppState = DashboardState() if has_profile else OnboardingState()

    def transition(self, next_state: AppState) -> AppState:
        self.state = next_state
        return self.state
