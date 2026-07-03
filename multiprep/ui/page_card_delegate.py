from __future__ import annotations

from PySide6.QtCore import QRect, QSize, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen, QPixmap, QTransform
from PySide6.QtWidgets import QStyledItemDelegate, QStyle

from multiprep.models.page_model import PageItem
from multiprep.ui.styles import is_gmail_mode


CARD_SIZE = QSize(226, 334)
CARD_RECT = QRect(6, 0, 214, 334)
IMAGE_RECT = QRect(18, 22, 190, 218)
TITLE_RECT = QRect(18, 250, 190, 76)


class PageCardDelegate(QStyledItemDelegate):
    """Paint page cards without creating hundreds of child widgets."""

    def sizeHint(self, _option, _index) -> QSize:
        return CARD_SIZE

    def paint(self, painter: QPainter, option, index) -> None:
        page: PageItem | None = index.data(Qt.ItemDataRole.UserRole)
        if page is None:
            return

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        selected = bool(option.state & QStyle.StateFlag.State_Selected)
        gmail_mode = is_gmail_mode()
        source_color = QColor(page.source.color)
        background = QColor(source_color)
        background.setAlpha(48 if gmail_mode else (95 if selected else 45))
        border = QColor("#202124" if gmail_mode else "#f9fafb") if selected else source_color

        card = CARD_RECT.translated(option.rect.topLeft())
        path = QPainterPath()
        path.addRoundedRect(card, 8, 8)
        painter.fillPath(path, background)
        painter.setPen(QPen(border, 3))
        painter.drawPath(path)

        bar = QRect(card.left() + 8, card.top() + 8, 198, 6)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(source_color)
        painter.drawRoundedRect(bar, 3, 3)

        image_rect = IMAGE_RECT.translated(option.rect.topLeft())
        painter.fillRect(image_rect, QColor("#ffffff"))
        pixmap = QPixmap(str(page.thumbnail_path))
        if not pixmap.isNull():
            if page.rotation % 360:
                pixmap = pixmap.transformed(QTransform().rotate(page.rotation % 360))
            pixmap = pixmap.scaled(
                image_rect.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.FastTransformation,
            )
            target = QRect(
                image_rect.center().x() - pixmap.width() // 2,
                image_rect.center().y() - pixmap.height() // 2,
                pixmap.width(),
                pixmap.height(),
            )
            painter.drawPixmap(target, pixmap)

        painter.setPen(QColor("#202124" if gmail_mode else "#f9fafb"))
        painter.setFont(QFont("Segoe UI", 9))
        title_rect = TITLE_RECT.translated(option.rect.topLeft())
        painter.drawText(
            title_rect,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap,
            self._title(page, index.row() + 1),
        )
        painter.restore()

    @staticmethod
    def _title(page: PageItem, number: int) -> str:
        if page.page_type == "capture":
            return f"{number}. Capture"
        if page.page_type == "image":
            return f"{number}. Image - {page.source.display_name}"
        if page.is_separator:
            return f"{number}. Séparateur - {page.source.display_stem}"
        return f"{number}. {page.source.display_name}"
