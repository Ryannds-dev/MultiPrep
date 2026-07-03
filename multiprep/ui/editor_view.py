from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from multiprep.ui.date_widgets import DateSpin
from multiprep.ui.page_board import PageBoard
from multiprep.ui.page_preview import PagePreviewPanel
from multiprep.utils.paths import APP_LOGO_PATH, CLASSIC_LOGO_PATH, resource_path


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
        mode_changed: Callable[[bool], None],
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
        self.mode_changed = mode_changed
        self.gmail_mode = True
        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        layout.addWidget(self._brand_header())
        layout.addLayout(self._toolbar())
        self.gmail_guide = self._gmail_guide()
        layout.addWidget(self.gmail_guide)
        self.classic_guide = self._classic_guide()
        layout.addWidget(self.classic_guide)

        self.preview = PagePreviewPanel()
        self.board.selected_page_changed.connect(self.preview.set_page)
        self.content_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.content_splitter.setChildrenCollapsible(False)
        self.content_splitter.addWidget(self.board)
        self.content_splitter.addWidget(self.preview)
        self.content_splitter.setStretchFactor(0, 3)
        self.content_splitter.setStretchFactor(1, 2)
        self.content_splitter.setSizes([720, 520])
        layout.addWidget(self.content_splitter, 1)
        self.set_gmail_mode(True)

    def _brand_header(self) -> QFrame:
        header = QFrame()
        header.setObjectName("BrandHeader")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(16, 10, 16, 10)

        self.logo = QLabel()
        self.logo.setFixedSize(58, 58)
        layout.addWidget(self.logo)

        titles = QVBoxLayout()
        title = QLabel("MultiPrep")
        title.setObjectName("BrandTitle")
        self.version_label = QLabel()
        self.version_label.setObjectName("BrandVersion")
        titles.addWidget(title)
        titles.addWidget(self.version_label)
        layout.addLayout(titles)
        layout.addStretch()

        self.mode_button = QPushButton()
        self.mode_button.setObjectName("ModeButton")
        self.mode_button.clicked.connect(self._toggle_mode)
        layout.addWidget(self.mode_button)
        return header

    def _toolbar(self) -> QHBoxLayout:
        top = QHBoxLayout()
        self.import_button = QPushButton("Importer des fichiers")
        self.import_button.setObjectName("SecondaryButton")
        self.import_button.clicked.connect(self.choose_pdfs)
        generate_button = QPushButton("Générer PDF")
        generate_button.clicked.connect(self.generate_pdf)

        widgets = self._field_widgets()
        stretch_before = len(widgets) - 2
        for index, widget in enumerate(widgets + [self.import_button, generate_button]):
            if index == stretch_before:
                top.addStretch()
            top.addWidget(widget)
        return top

    def _gmail_guide(self) -> QFrame:
        guide = QFrame()
        guide.setObjectName("GmailGuide")
        layout = QHBoxLayout(guide)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(24)

        title = QLabel("MODE GMAIL")
        title.setObjectName("GuideTitle")
        layout.addWidget(title)

        attachments = QLabel(
            "<b>Pièces jointes</b><br>"
            "Glissez directement les fichiers dans le grand espace ci-dessous."
        )
        attachments.setObjectName("MutedText")
        layout.addWidget(attachments)

        images = QLabel(
            "<b>Images dans le corps du mail Gmail</b><br>"
            "Copiez l’image affichée dans le message, puis utilisez <b>Ctrl+V</b><br>"
            "ou clic droit → Coller dans MultiPrep."
        )
        images.setObjectName("MutedText")
        layout.addWidget(images)
        layout.addStretch()
        return guide

    def _classic_guide(self) -> QFrame:
        guide = QFrame()
        guide.setObjectName("ClassicGuide")
        layout = QHBoxLayout(guide)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(24)

        title = QLabel("MODE CLASSIQUE")
        title.setObjectName("ClassicGuideTitle")
        layout.addWidget(title)
        files = QLabel(
            "<b>Fichiers locaux et applications de bureau</b><br>"
            "Importez depuis l’Explorateur, le Bureau ou une application de bureau (dont Outlook).<br>"
            "PDF · Word (.doc/.docx) · JPG · PNG"
        )
        files.setObjectName("MutedText")
        layout.addWidget(files)
        clipboard = QLabel(
            "<b>Différence avec le mode Gmail</b><br>"
            "Pour les pièces jointes de Gmail dans un navigateur, passez au mode Gmail.<br>"
            "Les captures locales restent collables avec <b>Ctrl+V</b> ou clic droit → Coller."
        )
        clipboard.setObjectName("MutedText")
        layout.addWidget(clipboard)
        layout.addStretch()
        return guide

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

    def _toggle_mode(self) -> None:
        self.set_gmail_mode(not self.gmail_mode)
        self.mode_changed(self.gmail_mode)

    def set_gmail_mode(self, enabled: bool) -> None:
        self.gmail_mode = enabled
        self.gmail_guide.setVisible(enabled)
        self.classic_guide.setVisible(not enabled)
        self.import_button.setVisible(not enabled)
        logo_path = APP_LOGO_PATH if enabled else CLASSIC_LOGO_PATH
        pixmap = QPixmap(str(resource_path(logo_path)))
        self.logo.setPixmap(
            pixmap.scaled(
                58,
                58,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
        self.version_label.setText(
            "VERSION 2.0.0 · GOOGLE WORKSPACE" if enabled else "VERSION 2.0.0 · MODE CLASSIQUE"
        )
        self.mode_button.setText("Passer au mode classique" if enabled else "Passer au mode Gmail")
