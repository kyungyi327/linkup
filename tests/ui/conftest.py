from __future__ import annotations

import os

import pytest
from PySide6.QtWidgets import QApplication

from linkup.ui.port import Exercise, Routine

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture(scope="session")
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def sample_routine() -> Routine:
    return Routine(
        items=[
            Exercise(
                ex_id="ex-1",
                name="첫 번째 운동",
                target_muscle="목",
                duration_text="30초",
                intensity="낮음",
                guide="천천히 움직입니다.",
            ),
            Exercise(
                ex_id="ex-2",
                name="두 번째 운동",
                target_muscle="어깨",
                duration_text="10회",
                intensity="보통",
                guide="호흡을 유지합니다.",
            ),
        ],
        expected_minutes=8,
    )
