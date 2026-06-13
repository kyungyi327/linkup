from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from linkup.ui.app import create_main_window
from linkup.ui.mock import MockDataProvider
from linkup.ui.view_model import AppViewModel


def main() -> None:
    application = QApplication(sys.argv)
    view_model = AppViewModel(MockDataProvider())
    window = create_main_window(view_model)
    window.show()
    sys.exit(application.exec())


if __name__ == "__main__":
    main()
