from __future__ import annotations

from linkup.ui.port import Exercise, Routine
from linkup.ui.state import (
    AppStateMachine,
    DailyLogState,
    DashboardState,
    ExerciseExecutionState,
    HistoryState,
    OnboardingState,
    ProfileEditState,
    RoutineLoadingState,
    RoutinePreviewState,
    SessionCompleteState,
)


def test_state_machine_initial_screen_depends_on_profile() -> None:
    assert isinstance(AppStateMachine(has_profile=True).state, DashboardState)
    assert AppStateMachine(has_profile=True).state.screen_key == "dashboard"
    assert isinstance(AppStateMachine(has_profile=False).state, OnboardingState)
    assert AppStateMachine(has_profile=False).state.screen_key == "onboarding"


def test_state_machine_transition_returns_and_stores_next_state() -> None:
    machine = AppStateMachine(has_profile=True)
    next_state = DailyLogState()

    returned = machine.transition(next_state)

    assert returned is next_state
    assert machine.state is next_state


def test_dashboard_routes_to_child_screens_and_clamps_routine_minutes() -> None:
    state = DashboardState()

    assert isinstance(state.open_condition(), DailyLogState)
    assert isinstance(state.open_history(), HistoryState)
    assert isinstance(state.open_profile(), ProfileEditState)
    assert state.start_routine_loading(1).available_min == 3
    assert state.start_routine_loading(7, "준비 중").available_min == 7
    assert state.start_routine_loading(99).available_min == 10
    assert state.start_routine_loading(7, "준비 중").message == "준비 중"


def test_profile_and_history_states_return_to_dashboard() -> None:
    assert isinstance(OnboardingState().profile_saved(), DashboardState)
    assert isinstance(DailyLogState().condition_done(), DashboardState)
    assert isinstance(ProfileEditState().profile_saved(), DashboardState)
    assert isinstance(ProfileEditState().cancel(), DashboardState)
    assert isinstance(HistoryState().back(), DashboardState)


def test_routine_loading_moves_to_preview(sample_routine: Routine) -> None:
    state = RoutineLoadingState(available_min=5, message="로딩")

    preview = state.routine_loaded(sample_routine)

    assert isinstance(preview, RoutinePreviewState)
    assert preview.routine is sample_routine
    assert preview.screen_key == "routine_preview"


def test_exercise_execution_progresses_and_completes_session(
    sample_routine: Routine,
) -> None:
    preview = RoutinePreviewState(sample_routine)
    exercise_state = preview.start_session("session-1")

    assert isinstance(exercise_state, ExerciseExecutionState)
    assert exercise_state.current_exercise() is sample_routine.items[0]

    replacement = Exercise(
        ex_id="ex-1-easy",
        name="쉬운 첫 번째 운동",
        target_muscle="목",
        duration_text="20초",
        intensity="낮음",
        guide="범위를 줄입니다.",
    )
    modified = exercise_state.exercise_modified(replacement)
    assert modified.modified_exercise is replacement

    next_exercise = modified.exercise_completed()
    assert isinstance(next_exercise, ExerciseExecutionState)
    assert next_exercise.exercise_index == 1
    assert next_exercise.modified_exercise is None
    assert next_exercise.current_exercise() is sample_routine.items[1]

    completed = next_exercise.exercise_completed()
    assert isinstance(completed, SessionCompleteState)
    assert completed.routine is sample_routine
    assert completed.session_id == "session-1"
    assert isinstance(completed.finish(), DashboardState)
    assert isinstance(completed.home(), DashboardState)


def test_routine_preview_can_go_back_to_dashboard(sample_routine: Routine) -> None:
    assert isinstance(RoutinePreviewState(sample_routine).back(), DashboardState)
