from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING

import pytest

from linkup.ui import form_loader

if TYPE_CHECKING:
    from collections.abc import Iterator


class FakeFile:
    OpenModeFlag = SimpleNamespace(ReadOnly=object())
    instances: list[FakeFile] = []
    should_open = True

    def __init__(self, path: str) -> None:
        self.path = path
        self.closed = False
        FakeFile.instances.append(self)

    def open(self, _mode: object) -> bool:
        return self.should_open

    def close(self) -> None:
        self.closed = True


class FakeLoader:
    loaded_widget: object | None = object()

    def load(self, file: FakeFile) -> object | None:
        assert file.path.endswith("MainWindow.ui")
        return self.loaded_widget


@contextmanager
def fake_as_file(_resource: object) -> Iterator[Path]:
    yield Path("MainWindow.ui")


@pytest.fixture(autouse=True)
def reset_fakes(monkeypatch: pytest.MonkeyPatch) -> None:
    FakeFile.instances = []
    FakeFile.should_open = True
    FakeLoader.loaded_widget = object()
    monkeypatch.setattr(form_loader, "as_file", fake_as_file)
    monkeypatch.setattr(form_loader, "QFile", FakeFile)
    monkeypatch.setattr(form_loader, "QUiLoader", FakeLoader)


def test_load_form_returns_loaded_widget_and_closes_file() -> None:
    widget = form_loader.load_form("MainWindow.ui")

    assert widget is FakeLoader.loaded_widget
    assert len(FakeFile.instances) == 1
    assert FakeFile.instances[0].closed


def test_load_form_raises_when_file_cannot_open() -> None:
    FakeFile.should_open = False

    with pytest.raises(RuntimeError, match="cannot open form MainWindow.ui"):
        form_loader.load_form("MainWindow.ui")


def test_load_form_raises_when_loader_returns_none() -> None:
    FakeLoader.loaded_widget = None

    with pytest.raises(RuntimeError, match="cannot load form MainWindow.ui"):
        form_loader.load_form("MainWindow.ui")

    assert FakeFile.instances[0].closed
