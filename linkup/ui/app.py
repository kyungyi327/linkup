from __future__ import annotations

from contextlib import ExitStack
from datetime import date
from importlib.resources import as_file, files
from typing import cast

from PySide6.QtCore import QFile, QObject, QTimer, Signal
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import (
    QAbstractButton,
    QAbstractItemView,
    QButtonGroup,
    QComboBox,
    QDoubleSpinBox,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QWidget,
)

from linkup.data.interfaces import (
    DailyLog,
    DataProvider,
    Exercise,
    Routine,
    SessionSummary,
    UserProfile,
)
from linkup.state import (
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

ASSET_FILES = files("linkup.ui.assets")
FORM_FILES = files("linkup.ui.forms")
MENTAL_CONDITION_MAX = 10
FATIGUE_MAX = 10
GENDER_LABELS = {"male": "남", "female": "여"}
GENDER_VALUES = {"남": "male", "여": "female", "male": "male", "female": "female"}
BODY_PARTS = (
    ("목", "neck", "fatigueNeckOption_"),
    ("어깨", "shoulder", "fatigueShoulderOption_"),
    ("허리", "lower_back", "fatigueLowerBackOption_"),
    ("손목", "wrist", "fatigueWristOption_"),
    ("무릎", "knee", "fatigueKneeOption_"),
    ("발목", "ankle", "fatigueAnkleOption_"),
)
BODY_PART_LABEL_TO_KEY = {label: key for label, key, _prefix in BODY_PARTS}
PAIN_OPTIONS = tuple(label for label, _key, _prefix in BODY_PARTS)
FATIGUE_PART_KEYS = {label: key for label, key, _prefix in BODY_PARTS}
CURRENT_YEAR = date.today().year


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
            "conditionButtonText": (
                "컨디션 수정" if condition_entered else "컨디션 입력"
            ),
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
            "mentalConditionScore": log.mental_condition_score
            if log.mental_condition_score is not None
            else 5,
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
                mental_condition_score=max(
                    0, min(MENTAL_CONDITION_MAX, mental_condition_score)
                ),
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
        state = self._require_state(
            RoutineLoadingState, "routine loading state is required"
        )
        self._machine.transition(
            state.routine_loaded(self._provider.generate_routine(state.available_min))
        )
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
        state = self._require_state(
            RoutinePreviewState, "routine preview state is required"
        )
        self._machine.transition(
            state.start_session(self._provider.start_session(state.routine))
        )
        self._emit_changed()

    def complete_current_exercise(self) -> None:
        state = self._require_state(
            ExerciseExecutionState, "exercise state is required"
        )
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
        state = self._require_state(
            ExerciseExecutionState, "exercise state is required"
        )
        ex = state.current_exercise()
        self._machine.transition(
            state.exercise_modified(self._provider.get_modified_exercise(ex.ex_id))
        )
        self._emit_changed()

    def finish_session(self, difficulty: str, pain: str, memo: str) -> None:
        state = self._require_state(SessionCompleteState, "complete state is required")
        self._completion = self._provider.end_session(
            state.session_id, difficulty, pain, memo
        )
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
        selected_pain_points = [
            part_key for part_key in pain_points if part_key in valid_part_keys
        ]
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

    def _require_state[StateT](
        self, state_type: type[StateT], error_message: str
    ) -> StateT:
        state = self._machine.state
        if not isinstance(state, state_type):
            raise RuntimeError(error_message)
        return state

    def _routine_from_state(self) -> Routine | None:
        state = self._machine.state
        if isinstance(
            state, RoutinePreviewState | ExerciseExecutionState | SessionCompleteState
        ):
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


class AppWindowController(QObject):
    def __init__(self, view_model: AppViewModel) -> None:
        super().__init__()
        self._view_model = view_model
        self._resource_stack = ExitStack()
        self.window = cast(QMainWindow, load_form("MainWindow.ui"))
        self._stack = self._find(self.window, QStackedWidget, "screenStack")
        self._screens = {
            OnboardingState.screen_key: self._add_screen(
                "Onboarding.ui", "onboardingPage"
            ),
            DashboardState.screen_key: self._add_screen(
                "Dashboard.ui", "dashboardPage"
            ),
            DailyLogState.screen_key: self._add_screen("DailyLog.ui", "dailyLogPage"),
            RoutineLoadingState.screen_key: self._add_screen(
                "RoutineLoading.ui", "routineLoadingPage"
            ),
            RoutinePreviewState.screen_key: self._add_screen(
                "RoutinePreview.ui", "routinePreviewPage"
            ),
            ExerciseExecutionState.screen_key: self._add_screen(
                "ExerciseExecution.ui", "exerciseExecutionPage"
            ),
            SessionCompleteState.screen_key: self._add_screen(
                "SessionComplete.ui", "completePage"
            ),
            ProfileEditState.screen_key: self._add_screen(
                "ProfileEdit.ui", "profileEditPage"
            ),
            HistoryState.screen_key: self._add_screen("History.ui", "historyPage"),
        }
        self._apply_spinbox_arrow_stylesheet()
        self._button_groups: list[QButtonGroup] = []
        self._configure_option_groups()
        self._connect_actions()
        self._view_model.changed.connect(self.render)
        self.render()

    def _apply_spinbox_arrow_stylesheet(self) -> None:
        up_arrow = self._asset_url("spinbox-up.svg")
        down_arrow = self._asset_url("spinbox-down.svg")
        self.window.setStyleSheet(
            self.window.styleSheet()
            + f"""
QSpinBox::up-arrow,
QDoubleSpinBox::up-arrow {{
    image: url("{up_arrow}");
    width: 10px;
    height: 10px;
}}
QSpinBox::down-arrow,
QDoubleSpinBox::down-arrow {{
    image: url("{down_arrow}");
    width: 10px;
    height: 10px;
}}
"""
        )

    def _asset_url(self, name: str) -> str:
        asset_path = self._resource_stack.enter_context(as_file(ASSET_FILES / name))
        return asset_path.as_posix()

    def render(self) -> None:
        screen_key = self._view_model.screen
        self._stack.setCurrentWidget(self._screens[screen_key])
        self._render_dashboard()
        self._render_condition()
        self._render_loading()
        self._render_routine()
        self._render_exercise()
        self._render_complete()
        self._render_profile(self._screens[OnboardingState.screen_key])
        self._render_profile(self._screens[ProfileEditState.screen_key])
        self._render_history()

    def _add_screen(self, file_name: str, object_name: str) -> QWidget:
        screen = load_form(file_name)
        screen.setObjectName(object_name)
        self._stack.addWidget(screen)
        return screen

    def _connect_actions(self) -> None:
        dashboard = self._screens[DashboardState.screen_key]
        self._button(dashboard, "startWorkoutButton").clicked.connect(
            self._begin_routine_load
        )
        self._button(dashboard, "historyButton").clicked.connect(
            self._view_model.open_history
        )
        self._button(dashboard, "conditionButton").clicked.connect(
            self._view_model.open_condition
        )
        self._button(dashboard, "profileButton").clicked.connect(
            self._view_model.open_profile
        )

        daily_log = self._screens[DailyLogState.screen_key]
        self._button(daily_log, "saveButton").clicked.connect(self._save_condition)
        self._button(daily_log, "cancelButton").clicked.connect(
            self._view_model.cancel_condition
        )

        routine = self._screens[RoutinePreviewState.screen_key]
        self._button(routine, "backButton").clicked.connect(
            self._view_model.back_to_dashboard
        )
        self._button(routine, "startButton").clicked.connect(
            self._view_model.start_session
        )

        exercise = self._screens[ExerciseExecutionState.screen_key]
        self._button(exercise, "modifyButton").clicked.connect(
            self._view_model.request_modified_exercise
        )
        self._button(exercise, "nextButton").clicked.connect(
            self._view_model.complete_current_exercise
        )

        complete = self._screens[SessionCompleteState.screen_key]
        self._button(complete, "saveButton").clicked.connect(self._finish_session)
        self._button(complete, "homeButton").clicked.connect(
            self._view_model.back_to_dashboard
        )

        profile = self._screens[ProfileEditState.screen_key]
        self._button(profile, "saveButton").clicked.connect(
            lambda: self._save_profile(profile)
        )
        self._button(profile, "cancelButton").clicked.connect(
            self._view_model.back_to_dashboard
        )

        onboarding = self._screens[OnboardingState.screen_key]
        self._button(onboarding, "saveButton").clicked.connect(
            lambda: self._save_profile(onboarding)
        )

        history = self._screens[HistoryState.screen_key]
        self._button(history, "backButton").clicked.connect(
            self._view_model.back_to_dashboard
        )

    def _render_dashboard(self) -> None:
        page = self._screens[DashboardState.screen_key]
        data = self._view_model.dashboard
        self._label(page, "greetingLabel").setText(str(data["greeting"]))
        self._label(page, "conditionDetailLabel").setText(str(data["conditionDetail"]))
        self._label(page, "streakLabel").setText(str(data["streak"]))
        self._label(page, "completionRateLabel").setText(str(data["completionRate"]))
        self._label(page, "conditionStatusLabel").setText(str(data["conditionStatus"]))
        condition_button = self._button(page, "conditionButton")
        condition_button.setText(str(data["conditionButtonText"]))
        condition_button.setProperty("entered", data["conditionEntered"])
        self._spin_box(page, "routineAvailableMinutesEdit").setValue(
            int(data["routineAvailableMin"])
        )

    def _begin_routine_load(self) -> None:
        page = self._screens[DashboardState.screen_key]
        self._view_model.begin_routine_load(
            self._spin_box(page, "routineAvailableMinutesEdit").value()
        )
        QTimer.singleShot(0, self._view_model.complete_routine_load)

    def _render_condition(self) -> None:
        page = self._screens[DailyLogState.screen_key]
        data = self._view_model.condition
        self._set_checked_button(
            page, "mentalConditionOption_", str(data["mentalConditionScore"])
        )
        self._double_spin_box(page, "outdoorHoursEdit").setValue(
            float(str(data["outdoorHours"]))
        )
        fatigue_by_part = cast(dict[str, int], data["fatigueByPart"])
        for part_key, prefix in self._fatigue_button_prefixes().items():
            self._set_checked_button(
                page, prefix, str(fatigue_by_part.get(part_key, 3))
            )

    def _render_loading(self) -> None:
        page = self._screens[RoutineLoadingState.screen_key]
        data = self._view_model.loading
        self._label(page, "loadingMessageLabel").setText(str(data["message"]))

    def _render_routine(self) -> None:
        page = self._screens[RoutinePreviewState.screen_key]
        data = self._view_model.routine
        self._label(page, "summaryLabel").setText(str(data["summary"]))
        routine_list = self._find(page, QListWidget, "routineList")
        routine_list.clear()
        for item in cast(list[dict[str, object]], data["items"]):
            text = (
                f"{item['name']} · {item['targetMuscle']} · "
                f"{item['duration']} · {item['intensity']}"
            )
            routine_list.addItem(QListWidgetItem(text))

    def _render_exercise(self) -> None:
        page = self._screens[ExerciseExecutionState.screen_key]
        data = self._view_model.exercise
        self._label(page, "progressLabel").setText(str(data["progressText"]))
        progress = self._find(page, QProgressBar, "progressBar")
        progress.setMaximum(int(data["progressMax"]))
        progress.setValue(int(data["progressValue"]))
        self._label(page, "titleLabel").setText(str(data["title"]))
        self._label(page, "guideLabel").setText(str(data["guide"]))
        self._label(page, "remainingLabel").setText(str(data["remainingText"]))

    def _render_complete(self) -> None:
        page = self._screens[SessionCompleteState.screen_key]
        data = self._view_model.complete
        self._label(page, "durationLabel").setText(str(data["duration"]))
        self._label(page, "completedCountLabel").setText(str(data["completedCount"]))
        self._label(page, "streakLabel").setText(str(data["streak"]))
        self._set_combo_items(
            self._combo(page, "difficultyCombo"),
            cast(list[str], data["difficultyOptions"]),
            "적당해요",
        )
        self._set_combo_items(
            self._combo(page, "painCombo"),
            cast(list[str], data["painOptions"]),
            "없었어요",
        )

    def _render_profile(self, page: QWidget) -> None:
        data = self._view_model.profile
        self._line_edit(page, "nicknameEdit").setText(str(data["nickname"]))
        birth_year = self._spin_box(page, "birthYearEdit")
        birth_year.setMaximum(CURRENT_YEAR)
        birth_year.setValue(int(str(data["birthYear"])))
        self._spin_box(page, "heightEdit").setValue(int(str(data["height"])))
        self._spin_box(page, "weightEdit").setValue(int(str(data["weight"])))
        self._spin_box(page, "pushupMaxEdit").setValue(int(str(data["pushupMax"])))
        self._spin_box(page, "plankMaxSecEdit").setValue(int(str(data["plankMaxSec"])))
        self._spin_box(page, "squatMaxEdit").setValue(int(str(data["squatMax"])))
        self._set_checked_button(page, "genderOption_", str(data["gender"]))
        for option in cast(list[str], data["painOptions"]):
            check = page.findChild(QAbstractButton, f"pain{option}Check")
            if check is not None:
                check.setChecked(
                    BODY_PART_LABEL_TO_KEY[option]
                    in cast(list[str], data["painPoints"])
                )

    def _render_history(self) -> None:
        page = self._screens[HistoryState.screen_key]
        data = self._view_model.history
        self._label(page, "completionRateLabel").setText(str(data["completionRate"]))
        self._label(page, "streakLabel").setText(str(data["streak"]))
        self._label(page, "totalSessionsLabel").setText(str(data["totalSessions"]))
        self._label(page, "totalHoursLabel").setText(str(data["totalHours"]))
        table = self._find(page, QTableWidget, "historyTable")
        rows = cast(list[dict[str, object]], data["rows"])
        table.setRowCount(len(rows))
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(
            ["날짜", "동작", "시간", "강도", "통증", "메모"]
        )
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setShowGrid(False)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setVisible(False)
        for row_index, row in enumerate(rows):
            for column, key in enumerate(
                ["date", "exerciseCount", "duration", "difficulty", "pain", "memo"]
            ):
                table.setItem(row_index, column, QTableWidgetItem(str(row[key])))
            table.setRowHeight(row_index, 42)

    def _save_condition(self) -> None:
        page = self._screens[DailyLogState.screen_key]
        self._view_model.save_condition(
            int(self._selected_button_text(page, "mentalConditionOption_", "5")),
            self._double_spin_box(page, "outdoorHoursEdit").value(),
            self._selected_fatigue_by_part(page),
        )

    def _finish_session(self) -> None:
        page = self._screens[SessionCompleteState.screen_key]
        self._view_model.finish_session(
            self._combo(page, "difficultyCombo").currentText(),
            self._combo(page, "painCombo").currentText(),
            self._find(page, QTextEdit, "memoEdit").toPlainText(),
        )

    def _save_profile(self, page: QWidget) -> None:
        self._view_model.save_profile(
            self._line_edit(page, "nicknameEdit").text(),
            self._spin_box(page, "birthYearEdit").value(),
            self._selected_button_text(page, "genderOption_", "남"),
            self._selected_pain_points(page),
            self._spin_box(page, "pushupMaxEdit").value(),
            self._spin_box(page, "plankMaxSecEdit").value(),
            self._spin_box(page, "squatMaxEdit").value(),
            str(self._spin_box(page, "heightEdit").value()),
            str(self._spin_box(page, "weightEdit").value()),
        )

    def _selected_pain_points(self, page: QWidget) -> list[str]:
        selected: list[str] = []
        for option in PAIN_OPTIONS:
            check = page.findChild(QAbstractButton, f"pain{option}Check")
            if check is not None and check.isChecked():
                selected.append(BODY_PART_LABEL_TO_KEY[option])
        return selected or ["neck", "shoulder"]

    def _label(self, parent: QWidget, name: str) -> QLabel:
        return self._find(parent, QLabel, name)

    def _button(self, parent: QWidget, name: str) -> QPushButton:
        return self._find(parent, QPushButton, name)

    def _line_edit(self, parent: QWidget, name: str) -> QLineEdit:
        return self._find(parent, QLineEdit, name)

    def _combo(self, parent: QWidget, name: str) -> QComboBox:
        return self._find(parent, QComboBox, name)

    def _spin_box(self, parent: QWidget, name: str) -> QSpinBox:
        return self._find(parent, QSpinBox, name)

    def _double_spin_box(self, parent: QWidget, name: str) -> QDoubleSpinBox:
        return self._find(parent, QDoubleSpinBox, name)

    def _configure_option_groups(self) -> None:
        daily_log = self._screens[DailyLogState.screen_key]
        self._make_exclusive_group(daily_log, "mentalConditionOption_")
        for prefix in self._fatigue_button_prefixes().values():
            self._make_exclusive_group(daily_log, prefix)

        for screen_key in (OnboardingState.screen_key, ProfileEditState.screen_key):
            page = self._screens[screen_key]
            self._make_exclusive_group(page, "genderOption_")
            for option in PAIN_OPTIONS:
                button = page.findChild(QAbstractButton, f"pain{option}Check")
                if button is not None:
                    button.setCheckable(True)

    def _make_exclusive_group(self, parent: QWidget, prefix: str) -> None:
        buttons = self._buttons_by_prefix(parent, prefix)
        if not buttons:
            return
        group = QButtonGroup(self)
        group.setExclusive(True)
        for button in buttons:
            button.setCheckable(True)
            group.addButton(button)
        self._button_groups.append(group)

    def _buttons_by_prefix(self, parent: QWidget, prefix: str) -> list[QAbstractButton]:
        return [
            button
            for button in parent.findChildren(QAbstractButton)
            if button.objectName().startswith(prefix)
        ]

    def _set_checked_button(
        self, parent: QWidget, prefix: str, selected_text: str
    ) -> None:
        buttons = self._buttons_by_prefix(parent, prefix)
        if not buttons:
            return
        selected_button = next(
            (button for button in buttons if button.text() == selected_text),
            buttons[0],
        )
        selected_button.setChecked(True)

    def _selected_button_text(self, parent: QWidget, prefix: str, fallback: str) -> str:
        for button in self._buttons_by_prefix(parent, prefix):
            if button.isChecked():
                return button.text()
        return fallback

    def _selected_fatigue_by_part(self, page: QWidget) -> dict[str, int]:
        return {
            part_key: int(self._selected_button_text(page, prefix, "3"))
            for part_key, prefix in self._fatigue_button_prefixes().items()
        }

    def _fatigue_button_prefixes(self) -> dict[str, str]:
        return {key: prefix for _label, key, prefix in BODY_PARTS}

    def _set_combo_items(
        self, combo: QComboBox, options: list[str], current_text: str
    ) -> None:
        if [combo.itemText(i) for i in range(combo.count())] != options:
            combo.clear()
            combo.addItems(options)
        self._set_combo_text(combo, current_text)

    def _set_combo_text(self, combo: QComboBox, current_text: str) -> None:
        index = combo.findText(current_text)
        combo.setCurrentIndex(max(index, 0))

    def _find[T: QWidget](self, parent: QWidget, widget_type: type[T], name: str) -> T:
        widget = parent.findChild(widget_type, name)
        if widget is None:
            raise RuntimeError(f"missing widget {name}")
        return widget


def load_form(name: str) -> QWidget:
    loader = QUiLoader()
    with as_file(FORM_FILES / name) as ui_path:
        file = QFile(str(ui_path))
        if not file.open(QFile.OpenModeFlag.ReadOnly):
            raise RuntimeError(f"cannot open form {name}")
        try:
            widget = loader.load(file)
        finally:
            file.close()
    if widget is None:
        raise RuntimeError(f"cannot load form {name}")
    return cast(QWidget, widget)


def create_main_window(view_model: AppViewModel) -> QMainWindow:
    controller = AppWindowController(view_model)
    controller.window.setProperty("controller", controller)
    return controller.window
