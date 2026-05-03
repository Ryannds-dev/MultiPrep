from __future__ import annotations

import ctypes
import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from multiprep.ui.main_window import MultiPrepWindow
from multiprep.utils.paths import APP_ICON_PATH, resource_path


def set_windows_app_id() -> None:
    if sys.platform != "win32":
        return
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("MultiPrep.MultiPrep")
    except Exception:
        pass


def main() -> None:
    set_windows_app_id()
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(str(resource_path(APP_ICON_PATH))))
    window = MultiPrepWindow()
    window.show()
    sys.exit(app.exec())
