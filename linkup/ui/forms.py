from __future__ import annotations

from importlib.resources import as_file
from typing import TYPE_CHECKING, cast

from PySide6.QtCore import QFile
from PySide6.QtUiTools import QUiLoader

from linkup.ui.constants import FORM_FILES

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget


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
    return cast("QWidget", widget)
