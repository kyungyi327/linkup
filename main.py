from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from linkup.data.mock_provider import MockDataProvider
from linkup.ui.app import AppViewModel, create_main_window


def main() -> None:
    application = QApplication(sys.argv)
    view_model = AppViewModel(MockDataProvider())
    window = create_main_window(view_model)
    window.show()
    sys.exit(application.exec())


if __name__ == "__main__":
    main()
