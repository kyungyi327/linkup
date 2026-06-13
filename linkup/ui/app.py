from __future__ import annotations

from typing import TYPE_CHECKING

from linkup.ui.controller import AppWindowController

if TYPE_CHECKING:
    from PySide6.QtWidgets import QMainWindow

    from linkup.ui.view_model import AppViewModel


def create_main_window(view_model: AppViewModel) -> QMainWindow:
    controller = AppWindowController(view_model)
    controller.window.setProperty("controller", controller)
    return controller.window
