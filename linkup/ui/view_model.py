from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from linkup.ui.constants import (
    FATIGUE_MAX,
    FATIGUE_PART_KEYS,
    GENDER_LABELS,
    GENDER_VALUES,
    MENTAL_CONDITION_MAX,
    PAIN_OPTIONS,
)
from linkup.ui.port import (
    DailyLog,
    DataProvider,
    Exercise,
    Routine,
    SessionSummary,
    UserProfile,
)
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


class AppViewModel(QObject):
    changed = Signal()

    def __init__(self, provider: DataProvider) -> None:
        super().__init__()
        self._provider = provider
        self._machine = AppStateMachine(has_profile=provider.has_user_profile())
        self._completion = SessionSummary(0, 0, 0)

    @property
    def screen(self) -> str:
        return self._machine.state.screen_key

    @property
    def dashboard(self) -> dict[str, object]:
        profile = self._current_or_default_profile()
        stats = self._provider.get_recent_stats()
        log = self._provider.get_today_log()
        condition_entered = log is not None
        return {
            "greeting": f"안녕하세요, {profile.nickname}님",
            "streak": f"{stats.streak_days}일",
            "completionRate": f"{self._completion_rate(stats.workout_days_7d)}%",
            "conditionStatus": "보통" if condition_entered else "미입력",
            "conditionDetail": self._condition_detail(log),
            "conditionButtonText": ("컨디션 수정" if condition_entered else "컨디션 입력"),
            "conditionEntered": condition_entered,
            "routineAvailableMin": 10,
        }

    @property
    def condition(self) -> dict[str, object]:
        log = self._provider.get_today_log()
        if log is None:
            return {
                "mentalConditionScore": 5,
                "outdoorHours": "1.0",
                "fatigueByPart": self._default_fatigue_by_part(),
            }
        return {
            "mentalConditionScore": log.mental_condition_score if log.mental_condition_score is not None else 5,
            "outdoorHours": str(log.outdoor_hours or 0),
            "fatigueByPart": log.fatigue_by_part,
        }

    @property
    def routine(self) -> dict[str, object]:
        routine = self._routine_from_state()
        if routine is None:
            return {"summary": "루틴 정보 없음", "items": []}
        return {
            "summary": f"예상 소요 시간: 약 {routine.expected_minutes}분",
            "items": [self._exercise_row(ex) for ex in routine.items],
        }

    @property
    def exercise(self) -> dict[str, object]:
        state = self._machine.state
        if not isinstance(state, ExerciseExecutionState):
            return {
                "progressText": "0 / 0",
                "progressValue": 0,
                "progressMax": 0,
                "title": "",
                "guide": "",
                "remainingText": "남은 동작 0",
            }
        routine = state.routine
        index = state.exercise_index
        current = routine.items[index]
        display = state.modified_exercise or current
        total = len(routine.items)
        done = index + 1
        return {
            "progressText": f"{done} / {total}",
            "progressValue": done,
            "progressMax": total,
            "title": display.name,
            "guide": display.guide,
            "remainingText": f"남은 동작 {total - index}",
        }

    @property
    def complete(self) -> dict[str, object]:
        return {
            "duration": f"{self._completion.duration_min}분",
            "completedCount": f"{self._completion.completed_count}개",
            "streak": f"{self._completion.streak_days}일",
            "difficultyOptions": ["쉬웠어요", "적당해요", "힘들었어요"],
            "painOptions": ["없었어요", "조금 있었어요"],
        }

    @property
    def profile(self) -> dict[str, object]:
        profile = self._current_or_default_profile()
        return {
            "nickname": profile.nickname,
            "birthYear": str(profile.birth_year or 2002),
            "gender": self._gender_label(profile.gender),
            "painPoints": profile.pain_points,
            "pushupMax": str(profile.pushup_max or 0),
            "plankMaxSec": str(profile.plank_max_sec or 0),
            "squatMax": str(profile.squat_max or 0),
            "height": str(profile.height_cm or 175),
            "weight": str(profile.weight_kg or 60),
            "genderOptions": ["남", "여"],
            "painOptions": list(PAIN_OPTIONS),
        }

    @property
    def history(self) -> dict[str, object]:
        stats = self._provider.get_recent_stats()
        return {
            "completionRate": f"{self._completion_rate(stats.workout_days_7d)}%",
            "streak": f"{stats.streak_days}일",
            "totalSessions": f"{stats.total_sessions}회",
            "totalHours": f"{stats.total_hours}h",
            "rows": [
                {
                    "date": row.date,
                    "exerciseCount": f"{row.exercise_count}개",
                    "duration": f"{row.duration_min}분",
                    "difficulty": row.difficulty_feedback,
                    "pain": row.pain_feedback,
                    "memo": row.memo,
                }
                for row in self._provider.get_session_list()
            ],
        }

    @property
    def loading(self) -> dict[str, object]:
        state = self._machine.state
        if isinstance(state, RoutineLoadingState):
            message = state.message
        else:
            message = "오늘 컨디션에 맞는 루틴을 준비하고 있어요"
        return {"message": message}

    def open_condition(self) -> None:
        state = self._require_state(DashboardState, "dashboard state is required")
        self._machine.transition(state.open_condition())
        self._emit_changed()

    def cancel_condition(self) -> None:
        state = self._require_state(DailyLogState, "daily log state is required")
        self._machine.transition(state.condition_done())
        self._emit_changed()

    def save_condition(
        self,
        mental_condition_score: int,
        outdoor_hours: float,
        fatigue_by_part: dict[str, int],
    ) -> None:
        valid_part_keys = set(FATIGUE_PART_KEYS.values())
        self._provider.upsert_today_log(
            DailyLog(
                mental_condition_score=max(0, min(MENTAL_CONDITION_MAX, mental_condition_score)),
                outdoor_hours=outdoor_hours,
                fatigue_by_part={
                    part_key: max(1, min(FATIGUE_MAX, value))
                    for part_key, value in fatigue_by_part.items()
                    if part_key in valid_part_keys
                },
            )
        )
        state = self._require_state(DailyLogState, "daily log state is required")
        self._machine.transition(state.condition_done())
        self._emit_changed()

    def begin_routine_load(self, available_min: int = 10) -> None:
        state = self._require_state(DashboardState, "dashboard state is required")
        self._machine.transition(state.start_routine_loading(available_min))
        self._emit_changed()

    def complete_routine_load(self) -> None:
        state = self._require_state(RoutineLoadingState, "routine loading state is required")
        self._machine.transition(state.routine_loaded(self._provider.generate_routine(state.available_min)))
        self._emit_changed()

    def open_routine(self) -> None:
        self.begin_routine_load()
        self.complete_routine_load()

    def back_to_dashboard(self) -> None:
        state = self._machine.state
        if isinstance(state, RoutinePreviewState | HistoryState):
            next_state = state.back()
        elif isinstance(state, ProfileEditState):
            next_state = state.cancel()
        elif isinstance(state, SessionCompleteState):
            next_state = state.home()
        else:
            next_state = DashboardState()
        self._machine.transition(next_state)
        self._emit_changed()

    def open_history(self) -> None:
        state = self._require_state(DashboardState, "dashboard state is required")
        self._machine.transition(state.open_history())
        self._emit_changed()

    def open_profile(self) -> None:
        state = self._require_state(DashboardState, "dashboard state is required")
        self._machine.transition(state.open_profile())
        self._emit_changed()

    def start_session(self) -> None:
        state = self._require_state(RoutinePreviewState, "routine preview state is required")
        self._machine.transition(state.start_session(self._provider.start_session(state.routine)))
        self._emit_changed()

    def complete_current_exercise(self) -> None:
        state = self._require_state(ExerciseExecutionState, "exercise state is required")
        ex = state.current_exercise()
        self._provider.record_history(state.session_id, ex.ex_id, True)
        self._machine.transition(state.exercise_completed())
        if isinstance(self._machine.state, SessionCompleteState):
            complete_state = self._machine.state
            stats = self._provider.get_recent_stats()
            self._completion = SessionSummary(
                duration_min=complete_state.routine.expected_minutes,
                completed_count=len(complete_state.routine.items),
                streak_days=stats.streak_days,
            )
        self._emit_changed()

    def request_modified_exercise(self) -> None:
        state = self._require_state(ExerciseExecutionState, "exercise state is required")
        ex = state.current_exercise()
        self._machine.transition(state.exercise_modified(self._provider.get_modified_exercise(ex.ex_id)))
        self._emit_changed()

    def finish_session(self, difficulty: str, pain: str, memo: str) -> None:
        state = self._require_state(SessionCompleteState, "complete state is required")
        self._completion = self._provider.end_session(state.session_id, difficulty, pain, memo)
        self._machine.transition(state.finish())
        self._emit_changed()

    def save_profile(
        self,
        nickname: str,
        birth_year: int,
        gender: str,
        pain_points: list[str],
        pushup_max: int,
        plank_max_sec: int,
        squat_max: int,
        height: str,
        weight: str,
    ) -> None:
        current = self._current_or_default_profile()
        valid_part_keys = set(FATIGUE_PART_KEYS.values())
        selected_pain_points = [part_key for part_key in pain_points if part_key in valid_part_keys]
        self._provider.save_user_profile(
            UserProfile(
                nickname=nickname or current.nickname,
                birth_year=birth_year,
                gender=self._gender_value(gender) or current.gender,
                pain_points=selected_pain_points or current.pain_points,
                pushup_max=pushup_max,
                plank_max_sec=plank_max_sec,
                squat_max=squat_max,
                height_cm=int(height or current.height_cm or 175),
                weight_kg=int(weight or current.weight_kg or 60),
            )
        )
        state = self._machine.state
        if isinstance(state, OnboardingState | ProfileEditState):
            self._machine.transition(state.profile_saved())
        else:
            raise RuntimeError("profile state is required")
        self._emit_changed()

    def _emit_changed(self) -> None:
        self.changed.emit()

    def _require_state[StateT](self, state_type: type[StateT], error_message: str) -> StateT:
        state = self._machine.state
        if not isinstance(state, state_type):
            raise RuntimeError(error_message)
        return state

    def _routine_from_state(self) -> Routine | None:
        state = self._machine.state
        if isinstance(state, RoutinePreviewState | ExerciseExecutionState | SessionCompleteState):
            return state.routine
        return None

    def _condition_detail(self, log: DailyLog | None) -> str:
        if log is None:
            return "컨디션 점수/부위별 피로도 정보 없음"
        fatigue_text = (
            ", ".join(
                f"{label} {log.fatigue_by_part[key]}/{FATIGUE_MAX}"
                for label, key in FATIGUE_PART_KEYS.items()
                if key in log.fatigue_by_part
            )
            or "부위별 피로도 정보 없음"
        )
        return (
            f"컨디션 {log.mental_condition_score or 0}/{MENTAL_CONDITION_MAX} · "
            f"외부활동 {log.outdoor_hours or 0:g}h · {fatigue_text}"
        )

    def _exercise_row(self, ex: Exercise) -> dict[str, object]:
        return {
            "name": ex.name,
            "targetMuscle": ex.target_muscle,
            "duration": ex.duration_text,
            "intensity": ex.intensity,
        }

    def _current_or_default_profile(self) -> UserProfile:
        if self._provider.has_user_profile():
            return self._provider.get_user_profile()
        return UserProfile(
            nickname="김동민",
            birth_year=2002,
            gender="male",
            pain_points=["neck", "shoulder"],
            pushup_max=12,
            plank_max_sec=60,
            squat_max=30,
            height_cm=175,
            weight_kg=59,
        )

    def _completion_rate(self, workout_days_7d: int) -> int:
        return round(max(0, min(7, workout_days_7d)) / 7 * 100)

    def _default_fatigue_by_part(self) -> dict[str, int]:
        return {key: 3 for key in FATIGUE_PART_KEYS.values()}

    def _gender_label(self, gender: str | None) -> str:
        return GENDER_LABELS.get(gender or "", "남")

    def _gender_value(self, gender: str) -> str | None:
        return GENDER_VALUES.get(gender)
