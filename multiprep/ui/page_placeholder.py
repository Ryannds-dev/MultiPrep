from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from multiprep.ui.styles import is_gmail_mode


CARD_WIDTH = 214
CARD_HEIGHT = 334


class PagePlaceholderWidget(QFrame):
    def __init__(self, count: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(CARD_WIDTH, CARD_HEIGHT)
        if is_gmail_mode():
            self.setStyleSheet(
                """
                PagePlaceholderWidget {
                    background: rgba(249, 171, 0, 35);
                    border: 3px dashed #f9ab00;
                    border-radius: 8px;
                }
                PagePlaceholderWidget QLabel {
                    color: #7a4f00;
                    background: transparent;
                    font-weight: 700;
                }
                """
            )
        else:
            self.setStyleSheet(
                """
                PagePlaceholderWidget {
                    background: rgba(96, 165, 250, 45);
                    border: 3px dashed #93c5fd;
                    border-radius: 8px;
                }
                PagePlaceholderWidget QLabel {
                    color: #dbeafe;
                    background: transparent;
                    font-weight: 700;
                }
                """
            )
        layout = QVBoxLayout(self)
        label = QLabel(f"{count} page(s)")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()
        layout.addWidget(label)
        layout.addStretch()
