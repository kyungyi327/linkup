from __future__ import annotations

import pytest
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QLabel,
    QPushButton,
    QWidget,
)

from linkup.ui.controller import AppWindowController


def _controller() -> AppWindowController:
    return AppWindowController.__new__(AppWindowController)


def test_guide_markup_escapes_html_and_preserves_line_breaks() -> None:
    controller = _controller()

    markup = controller._guide_markup("<b>주의</b>\n천천히")

    assert markup == ('<div style="line-height: 150%;">&lt;b&gt;주의&lt;/b&gt;<br>천천히</div>')


def test_button_helpers_select_by_prefix_and_text(qapp: QApplication) -> None:
    assert qapp is not None
    controller = _controller()
    parent = QWidget()
    first = QPushButton("1", parent)
    first.setObjectName("option_1")
    first.setCheckable(True)
    second = QPushButton("2", parent)
    second.setObjectName("option_2")
    second.setCheckable(True)
    unrelated = QPushButton("2", parent)
    unrelated.setObjectName("other_2")
    unrelated.setCheckable(True)

    buttons = controller._buttons_by_prefix(parent, "option_")
    controller._set_checked_button(parent, "option_", "2")

    assert buttons == [first, second]
    assert second.isChecked()
    assert not first.isChecked()
    assert not unrelated.isChecked()
    assert controller._selected_button_text(parent, "option_", "fallback") == "2"
    assert controller._selected_button_text(parent, "missing_", "fallback") == "fallback"


def test_button_helper_defaults_to_first_button_when_text_is_missing(
    qapp: QApplication,
) -> None:
    assert qapp is not None
    controller = _controller()
    parent = QWidget()
    first = QPushButton("1", parent)
    first.setObjectName("option_1")
    first.setCheckable(True)
    second = QPushButton("2", parent)
    second.setObjectName("option_2")
    second.setCheckable(True)

    controller._set_checked_button(parent, "option_", "9")

    assert first.isChecked()
    assert not second.isChecked()


def test_combo_helpers_replace_items_only_when_needed(qapp: QApplication) -> None:
    assert qapp is not None
    controller = _controller()
    combo = QComboBox()

    controller._set_combo_items(combo, ["쉬움", "보통", "어려움"], "보통")
    controller._set_combo_items(combo, ["쉬움", "보통", "어려움"], "어려움")

    assert combo.count() == 3
    assert combo.currentText() == "어려움"

    controller._set_combo_text(combo, "없음")

    assert combo.currentText() == "쉬움"


def test_selected_pain_points_returns_checked_keys_or_default(
    qapp: QApplication,
) -> None:
    assert qapp is not None
    controller = _controller()
    parent = QWidget()
    neck = QPushButton("목", parent)
    neck.setObjectName("pain목Check")
    neck.setCheckable(True)
    shoulder = QPushButton("어깨", parent)
    shoulder.setObjectName("pain어깨Check")
    shoulder.setCheckable(True)

    neck.setChecked(True)
    assert controller._selected_pain_points(parent) == ["neck"]

    neck.setChecked(False)
    assert controller._selected_pain_points(parent) == ["neck", "shoulder"]


def test_find_returns_named_widget_or_raises(qapp: QApplication) -> None:
    assert qapp is not None
    controller = _controller()
    parent = QWidget()
    label = QLabel("내용", parent)
    label.setObjectName("targetLabel")

    assert controller._find(parent, QLabel, "targetLabel") is label

    with pytest.raises(RuntimeError, match="missing widget missingLabel"):
        controller._find(parent, QLabel, "missingLabel")
