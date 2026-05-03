from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from multiprep.models.page_model import PageItem


class PageThumbnailWidget(QFrame):
    def __init__(self, item: PageItem, number: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.item = item
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.setFixedWidth(214)
        self.setStyleSheet(self._style(False))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        source_bar = QLabel()
        source_bar.setFixedHeight(6)
        source_bar.setStyleSheet(f"background: {item.source.color}; border-radius: 3px;")
        layout.addWidget(source_bar)

        image = QLabel()
        pixmap = QPixmap(str(item.thumbnail_path))
        image.setPixmap(pixmap)
        image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image.setFixedSize(190, 240)
        image.setStyleSheet("background: #ffffff; border-radius: 3px;")
        layout.addWidget(image, alignment=Qt.AlignmentFlag.AlignCenter)

        title = QLabel(self._title(item, number))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setWordWrap(True)
        title.setToolTip(item.display_name)
        layout.addWidget(title)

    def set_selected(self, selected: bool) -> None:
        self.setStyleSheet(self._style(selected))

    def _title(self, item: PageItem, number: int) -> str:
        if item.page_type == "capture":
            return f"{number}. Capture"
        if item.is_separator:
            return f"{number}. Separateur - {item.source.path.stem}"
        return f"{number}. {item.source.path.name}"

    def _style(self, selected: bool) -> str:
        border = "#f9fafb" if selected else self.item.source.color
        background_alpha = 95 if selected else 45
        color = QColor(self.item.source.color)
        return f"""
        PageThumbnailWidget {{
            background: rgba({color.red()}, {color.green()}, {color.blue()}, {background_alpha});
            border: 3px solid {border};
            border-radius: 8px;
        }}
        PageThumbnailWidget QLabel {{
            color: #f9fafb;
            background: transparent;
        }}
        """


class PagePlaceholderWidget(QFrame):
    def __init__(self, count: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(214, 334)
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
