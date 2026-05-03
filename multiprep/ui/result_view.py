from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from multiprep.ui.dialogs import DraggableFile


class ResultView(QWidget):
    cancel_requested = Signal()
    new_case_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(40, 40, 40, 40)
        self.layout.setSpacing(18)

    def show_output(self, output_path: Path) -> None:
        self._clear()
        title = QLabel("PDF généré")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 28px; font-weight: 700;")

        filename = QLabel(output_path.name)
        filename.setAlignment(Qt.AlignmentFlag.AlignCenter)
        filename.setWordWrap(True)

        hint = QLabel("Glissez ce fichier vers Multigest")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)

        file_zone = DraggableFile(output_path)
        file_zone.setMinimumHeight(120)

        self.layout.addStretch()
        for widget in (title, filename, hint, file_zone):
            self.layout.addWidget(widget)
        self.layout.addLayout(self._buttons())
        self.layout.addStretch()

    def _buttons(self) -> QHBoxLayout:
        buttons = QHBoxLayout()
        cancel = QPushButton("Annuler")
        cancel.clicked.connect(self.cancel_requested.emit)
        new_case = QPushButton("Nouveau dossier")
        new_case.clicked.connect(self.new_case_requested.emit)
        buttons.addWidget(cancel)
        buttons.addStretch()
        buttons.addWidget(new_case)
        return buttons

    def _clear(self) -> None:
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_child_layout(item.layout())

    def _clear_child_layout(self, layout: QHBoxLayout | QVBoxLayout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
