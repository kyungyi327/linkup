from __future__ import annotations

from importlib.resources import as_file
from typing import TYPE_CHECKING

from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import QApplication

from linkup.ui.constants import ASSET_FILES
from linkup.ui.controller import AppWindowController

if TYPE_CHECKING:
    from PySide6.QtWidgets import QMainWindow

    from linkup.ui.view_model import AppViewModel


def create_main_window(view_model: AppViewModel) -> QMainWindow:
    _install_application_font()
    controller = AppWindowController(view_model)
    controller.window.setProperty("controller", controller)
    return controller.window


def _install_application_font() -> None:
    with as_file(ASSET_FILES / "PretendardVariable.ttf") as font_path:
        font_id = QFontDatabase.addApplicationFont(str(font_path))
    if font_id < 0:
        return
    families = QFontDatabase.applicationFontFamilies(font_id)
    if families:
        QApplication.setFont(QFont(families[0]))
