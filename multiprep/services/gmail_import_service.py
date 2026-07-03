from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, QProcess, QTimer, Signal
from PySide6.QtWidgets import QWidget

from multiprep.utils.paths import MAIL_DROP_DIR, resource_path


GMAIL_HELPER = Path("assets") / "GmailDropHelper.exe"


class GmailImportService(QObject):
    files_ready = Signal(list)
    failed = Signal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.process: QProcess | None = None
        self.visible_at_start = False
        self.manifest_path = MAIL_DROP_DIR / "gmail_import.txt"
        self.poll_timer = QTimer(self)
        self.poll_timer.setInterval(250)
        self.poll_timer.timeout.connect(self._read_manifest)

    def attach_to(self, host: QWidget, visible: bool) -> None:
        if self.process is not None:
            if self.visible_at_start == visible:
                return
            self.stop()
        helper_path = resource_path(GMAIL_HELPER)
        if not helper_path.is_file():
            self.failed.emit("Le composant d’import Gmail est introuvable.")
            return

        MAIL_DROP_DIR.mkdir(parents=True, exist_ok=True)
        self.manifest_path.unlink(missing_ok=True)
        process = QProcess(self)
        process.errorOccurred.connect(self._process_error)
        process.finished.connect(self._process_finished)
        self.process = process
        self.visible_at_start = visible
        parent_window_id = int(host.winId())
        process.start(
            str(helper_path),
            [
                str(MAIL_DROP_DIR.resolve()),
                str(self.manifest_path.resolve()),
                str(parent_window_id),
                "1" if visible else "0",
            ],
        )
        self.poll_timer.start()

    def _read_manifest(self) -> None:
        if not self.manifest_path.is_file():
            return
        try:
            paths = [
                Path(line.strip())
                for line in self.manifest_path.read_text(encoding="utf-8-sig").splitlines()
                if line.strip()
            ]
            self.manifest_path.unlink(missing_ok=True)
        except OSError:
            return
        if paths:
            self.files_ready.emit(paths)

    def _process_finished(self, _exit_code: int, _exit_status) -> None:
        process = self.sender()
        if process is self.process:
            self.poll_timer.stop()
            self.process = None
            self.visible_at_start = False
        if isinstance(process, QProcess):
            process.deleteLater()

    def _process_error(self, _error) -> None:
        self.failed.emit("Impossible d’intégrer la zone de dépôt Gmail.")

    def stop(self) -> None:
        self.poll_timer.stop()
        if self.process is None:
            return
        process = self.process
        self.process = None
        self.visible_at_start = False
        process.finished.connect(process.deleteLater)
        process.kill()
