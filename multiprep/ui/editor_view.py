from __future__ import annotations

from collections.abc import Callable

from PySide6.QtWidgets import QCheckBox, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget

from multiprep.ui.date_widgets import DateSpin
from multiprep.ui.page_board import PageBoard


class EditorView(QWidget):
    def __init__(
        self,
        name_edit: QLineEdit,
        firstname_edit: QLineEdit,
        day_spin: DateSpin,
        month_spin: DateSpin,
        year_spin: DateSpin,
        suffix_check: QCheckBox,
        board: PageBoard,
        choose_pdfs: Callable[[], None],
        generate_pdf: Callable[[], None],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.name_edit = name_edit
        self.firstname_edit = firstname_edit
        self.day_spin = day_spin
        self.month_spin = month_spin
        self.year_spin = year_spin
        self.suffix_check = suffix_check
        self.board = board
        self.choose_pdfs = choose_pdfs
        self.generate_pdf = generate_pdf
        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        layout.addLayout(self._toolbar())
        layout.addWidget(self._paste_hint())
        layout.addWidget(self.board, 1)

    def _toolbar(self) -> QHBoxLayout:
        top = QHBoxLayout()
        import_button = QPushButton("Importer")
        import_button.clicked.connect(self.choose_pdfs)
        generate_button = QPushButton("Générer PDF")
        generate_button.clicked.connect(self.generate_pdf)

        widgets = self._field_widgets()
        stretch_before = len(widgets) - 2
        for index, widget in enumerate(widgets + [import_button, generate_button]):
            if index == stretch_before:
                top.addStretch()
            top.addWidget(widget)
        return top

    def _field_widgets(self) -> list[QWidget]:
        return [
            QLabel("Nom"),
            self.name_edit,
            QLabel("Prénom"),
            self.firstname_edit,
            QLabel("Date"),
            self.day_spin,
            self.month_spin,
            self.year_spin,
            QLabel("Suffixe"),
            self.suffix_check,
        ]

    def _paste_hint(self) -> QLabel:
        paste_hint = QLabel("Astuce : utilisez Ctrl + V ou clic droit -> Coller pour coller une capture d'écran du mail")
        paste_hint.setStyleSheet("color: #cbd5e1; font-size: 9pt;")
        return paste_hint
