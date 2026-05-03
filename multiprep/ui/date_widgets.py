from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QSpinBox, QToolButton, QWidget


class DateSpin(QWidget):
    class PaddedSpinBox(QSpinBox):
        def __init__(self, digits: int) -> None:
            super().__init__()
            self.digits = digits

        def textFromValue(self, value: int) -> str:
            return f"{value:0{self.digits}d}" if self.digits > 1 else str(value)

    def __init__(self, minimum: int, maximum: int, value: int, width: int, digits: int = 1) -> None:
        super().__init__()
        self.spin = self.PaddedSpinBox(digits)
        self.spin.setRange(minimum, maximum)
        self.spin.setValue(value)
        self.spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.spin.setFixedWidth(width)
        self.spin.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.spin.setKeyboardTracking(False)
        self._build_buttons()

    def value(self) -> int:
        return self.spin.value()

    def setValue(self, value: int) -> None:
        self.spin.setValue(value)

    def _build_buttons(self) -> None:
        minus = QToolButton()
        minus.setText("-")
        minus.setToolTip("Reduire")
        minus.clicked.connect(lambda: self.spin.stepBy(-1))
        plus = QToolButton()
        plus.setText("+")
        plus.setToolTip("Augmenter")
        plus.clicked.connect(lambda: self.spin.stepBy(1))
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)
        layout.addWidget(minus)
        layout.addWidget(self.spin)
        layout.addWidget(plus)
