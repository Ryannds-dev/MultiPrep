from __future__ import annotations

import fitz
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QTransform
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy, QToolButton, QVBoxLayout, QWidget

from multiprep.models.page_model import PageItem

PREVIEW_RENDER_WIDTH = 1400


class PagePreviewPanel(QFrame):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._expanded = True
        self._pixmap: QPixmap | None = None
        self.setMinimumWidth(420)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.apply_theme(True)
        self._build()

    def set_page(self, page: PageItem | None) -> None:
        if page is None:
            self.title.setText("Aucune page sélectionnée")
            self.image.setPixmap(QPixmap())
            self._pixmap = None
            return
        self.title.setText(page.display_name)
        self._pixmap = self._render_page(page)
        self._refresh_image()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._refresh_image()

    def _build(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        self.toggle = QToolButton()
        self.toggle.setText(">")
        self.toggle.setToolTip("Replier / ouvrir la prévisualisation")
        self.toggle.clicked.connect(self._toggle)
        root.addWidget(self.toggle, alignment=Qt.AlignmentFlag.AlignTop)

        self.content = QWidget()
        content_layout = QVBoxLayout(self.content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(10)

        self.title = QLabel("Aucune page sélectionnée")
        self.title.setWordWrap(True)
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.image = QLabel()
        self.image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image.setMinimumSize(360, 520)
        self.image.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.image.setStyleSheet("background: #ffffff; border-radius: 4px;")

        content_layout.addWidget(self.title)
        content_layout.addWidget(self.image, 1)
        root.addWidget(self.content, 1)

    def _toggle(self) -> None:
        self._expanded = not self._expanded
        self.content.setVisible(self._expanded)
        if self._expanded:
            self.setMaximumWidth(16777215)
            self.setMinimumWidth(420)
        else:
            self.setFixedWidth(48)
        self.toggle.setText(">" if self._expanded else "<")
        self._refresh_image()

    def _refresh_image(self) -> None:
        if self._pixmap is None or self._pixmap.isNull() or not self._expanded:
            return
        size = self.image.size()
        scaled = self._pixmap.scaled(
            size.width() - 10,
            size.height() - 10,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.image.setPixmap(scaled)

    def _render_page(self, page: PageItem) -> QPixmap:
        try:
            with fitz.open(page.source.path) as document:
                pdf_page = document[page.page_index]
                zoom = PREVIEW_RENDER_WIDTH / pdf_page.rect.width
                pixmap = pdf_page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
                preview = QPixmap()
                if preview.loadFromData(pixmap.tobytes("png")):
                    if page.rotation % 360:
                        preview = preview.transformed(QTransform().rotate(page.rotation % 360))
                    return preview
        except Exception:
            pass
        return QPixmap(str(page.thumbnail_path))

    def _style(self) -> str:
        return """
        PagePreviewPanel {
            background: #0f172a;
            border: 1px solid #374151;
            border-radius: 6px;
        }
        PagePreviewPanel QLabel {
            color: #f9fafb;
            background: transparent;
        }
        """

    def apply_theme(self, gmail_mode: bool) -> None:
        if gmail_mode:
            self.setStyleSheet(
                """
                PagePreviewPanel {
                    background: #ffffff;
                    border: 1px solid #eadfbf;
                    border-radius: 10px;
                }
                PagePreviewPanel QLabel { color: #202124; background: transparent; }
                """
            )
        else:
            self.setStyleSheet(self._style())
