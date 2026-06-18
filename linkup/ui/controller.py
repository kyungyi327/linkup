from __future__ import annotations

from contextlib import ExitStack
from html import escape
from importlib.resources import as_file
from typing import TYPE_CHECKING, cast

from PySide6.QtCore import QObject, Qt, QTimer
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
    QProgressBar,
    QPushButton,
    QSpinBox,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QWidget,
)

from linkup.ui.constants import (
    ASSET_FILES,
    BODY_PART_LABEL_TO_KEY,
    BODY_PARTS,
    CURRENT_YEAR,
    PAIN_OPTIONS,
)
from linkup.ui.form_loader import load_form
from linkup.ui.state import (
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

if TYPE_CHECKING:
    from PySide6.QtWidgets import QMainWindow

    from linkup.ui.view_model import AppViewModel


class AppWindowController(QObject):
    def __init__(self, view_model: AppViewModel) -> None:
        super().__init__()
        self._view_model = view_model
        self._resource_stack = ExitStack()
        self.window = cast("QMainWindow", load_form("MainWindow.ui"))
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
        self._apply_stylesheet()
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

    def _apply_stylesheet(self) -> None:
        self.window.setStyleSheet((ASSET_FILES / "app.qss").read_text("utf-8"))

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
        fatigue_by_part = cast("dict[str, int]", data["fatigueByPart"])
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
        for item in cast("list[dict[str, object]]", data["items"]):
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
        guide_label = self._label(page, "guideLabel")
        guide_label.setTextFormat(Qt.TextFormat.RichText)
        guide_label.setText(self._guide_markup(str(data["guide"])))
        self._label(page, "remainingLabel").setText(str(data["remainingText"]))

    def _render_complete(self) -> None:
        page = self._screens[SessionCompleteState.screen_key]
        data = self._view_model.complete
        self._label(page, "durationLabel").setText(str(data["duration"]))
        self._label(page, "completedCountLabel").setText(str(data["completedCount"]))
        self._label(page, "streakLabel").setText(str(data["streak"]))
        self._set_combo_items(
            self._combo(page, "difficultyCombo"),
            cast("list[str]", data["difficultyOptions"]),
            "적당해요",
        )
        self._set_combo_items(
            self._combo(page, "painCombo"),
            cast("list[str]", data["painOptions"]),
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
        for option in cast("list[str]", data["painOptions"]):
            check = page.findChild(QAbstractButton, f"pain{option}Check")
            if check is not None:
                check.setChecked(
                    BODY_PART_LABEL_TO_KEY[option]
                    in cast("list[str]", data["painPoints"])
                )

    def _render_history(self) -> None:
        page = self._screens[HistoryState.screen_key]
        data = self._view_model.history
        self._label(page, "completionRateLabel").setText(str(data["completionRate"]))
        self._label(page, "streakLabel").setText(str(data["streak"]))
        self._label(page, "totalSessionsLabel").setText(str(data["totalSessions"]))
        self._label(page, "totalHoursLabel").setText(str(data["totalHours"]))
        table = self._find(page, QTableWidget, "historyTable")
        rows = cast("list[dict[str, object]]", data["rows"])
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

    def _guide_markup(self, text: str) -> str:
        guide = escape(text).replace("\n", "<br>")
        return f'<div style="line-height: 150%;">{guide}</div>'

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
