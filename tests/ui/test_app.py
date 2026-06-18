from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtWidgets import QApplication, QWidget

from linkup.ui import app as app_module

if TYPE_CHECKING:
    from collections.abc import Iterator

    import pytest


class DummyController:
    def __init__(self, view_model: object) -> None:
        self.view_model = view_model
        self.window = QWidget()


def test_create_main_window_installs_font_and_attaches_controller(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert qapp is not None
    installed: list[str] = []
    view_model = object()

    monkeypatch.setattr(
        app_module,
        "_install_application_font",
        lambda: installed.append("font"),
    )
    monkeypatch.setattr(app_module, "AppWindowController", DummyController)

    window = app_module.create_main_window(view_model)

    controller = window.property("controller")
    assert installed == ["font"]
    assert isinstance(controller, DummyController)
    assert controller.view_model is view_model
    assert controller.window is window


def test_install_application_font_sets_first_available_family(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    set_fonts: list[object] = []

    @contextmanager
    def fake_as_file(_resource: object) -> Iterator[Path]:
        yield Path("PretendardVariable.ttf")

    monkeypatch.setattr(app_module, "as_file", fake_as_file)
    monkeypatch.setattr(app_module.QFontDatabase, "addApplicationFont", lambda _path: 1)
    monkeypatch.setattr(
        app_module.QFontDatabase,
        "applicationFontFamilies",
        lambda _font_id: ["Pretendard"],
    )
    monkeypatch.setattr(app_module, "QFont", lambda family: ("font", family))
    monkeypatch.setattr(app_module.QApplication, "setFont", set_fonts.append)

    app_module._install_application_font()

    assert set_fonts == [("font", "Pretendard")]


def test_install_application_font_ignores_failed_font_load(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    @contextmanager
    def fake_as_file(_resource: object) -> Iterator[Path]:
        yield Path("missing.ttf")

    monkeypatch.setattr(app_module, "as_file", fake_as_file)
    monkeypatch.setattr(
        app_module.QFontDatabase,
        "addApplicationFont",
        lambda _path: -1,
    )
    monkeypatch.setattr(
        app_module.QFontDatabase,
        "applicationFontFamilies",
        lambda _font_id: calls.append("families"),
    )
    monkeypatch.setattr(
        app_module.QApplication,
        "setFont",
        lambda _font: calls.append("set"),
    )

    app_module._install_application_font()

    assert calls == []
