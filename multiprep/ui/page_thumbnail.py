from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from multiprep.models.page_model import PageItem

TITLE_WIDTH = 190
TITLE_HEIGHT = 78
CARD_WIDTH = 214
CARD_HEIGHT = 334
IMAGE_HEIGHT = 218
MAX_WORD_LENGTH = 24


class PageThumbnailWidget(QFrame):
    def __init__(self, item: PageItem, number: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.item = item
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.setFixedSize(CARD_WIDTH, CARD_HEIGHT)
        self.setStyleSheet(self._style(False))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(0)

        source_bar = QLabel()
        source_bar.setFixedHeight(6)
        source_bar.setStyleSheet(f"background: {item.source.color}; border-radius: 3px;")
        layout.addWidget(source_bar)
        layout.addSpacing(6)

        image = QLabel()
        pixmap = QPixmap(str(item.thumbnail_path))
        image.setPixmap(pixmap.scaled(TITLE_WIDTH, IMAGE_HEIGHT, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image.setFixedSize(TITLE_WIDTH, IMAGE_HEIGHT)
        image.setStyleSheet("background: #ffffff; border-radius: 3px;")
        layout.addWidget(image, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(10)

        title = QLabel()
        title.setFixedSize(TITLE_WIDTH, TITLE_HEIGHT)
        title.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        title.setWordWrap(True)
        title.setToolTip(item.display_name)
        title.setText(self._wrap_long_words(self._title(item, number)))
        layout.addWidget(title)

    def set_selected(self, selected: bool) -> None:
        self.setStyleSheet(self._style(selected))

    def _title(self, item: PageItem, number: int) -> str:
        if item.page_type == "capture":
            return f"{number}. Capture"
        if item.page_type == "image":
            return f"{number}. Image - {item.source.display_name}"
        if item.is_separator:
            return f"{number}. Separateur - {item.source.display_stem}"
        return f"{number}. {item.source.display_name}"

    def _wrap_long_words(self, title: str) -> str:
        parts = title.replace("_", "_ ").replace("-", "- ").split(" ")
        wrapped = [self._wrap_word(part) for part in parts]
        return " ".join(part for part in wrapped if part)

    def _wrap_word(self, word: str) -> str:
        if len(word) <= MAX_WORD_LENGTH:
            return word
        chunks = [word[index:index + MAX_WORD_LENGTH] for index in range(0, len(word), MAX_WORD_LENGTH)]
        return "\n".join(chunks)


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
        self.setFixedSize(CARD_WIDTH, CARD_HEIGHT)
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
