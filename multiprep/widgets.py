from __future__ import annotations

import shutil
import tempfile
from pathlib import PureWindowsPath
from pathlib import Path
from typing import Optional
from uuid import uuid4

from PySide6.QtCore import QByteArray, QMimeData, QPoint, QSize, Qt, QUrl, Signal
from PySide6.QtGui import QAction, QColor, QDrag, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from .models import PageItem, SeparatorOption


PAGE_MIME = "application/x-multiprep-page-indexes"
FILE_MIME = "text/uri-list"
MAIL_DROP_DIR = Path(tempfile.mkdtemp(prefix="multiprep_mail_attachments_"))


def has_pdf_mime(mime_data: QMimeData) -> bool:
    if _local_pdf_paths(mime_data):
        return True
    return any(name.lower().endswith(".pdf") for name in _windows_attachment_names(mime_data))


def pdf_paths_from_mime(mime_data: QMimeData) -> list[Path]:
    local_paths = _local_pdf_paths(mime_data)
    if local_paths:
        return local_paths
    return _extract_windows_pdf_attachments(mime_data)


def cleanup_mail_drop_dir() -> None:
    shutil.rmtree(MAIL_DROP_DIR, ignore_errors=True)


def _local_pdf_paths(mime_data: QMimeData) -> list[Path]:
    if not mime_data.hasUrls():
        return []
    return [
        Path(url.toLocalFile())
        for url in mime_data.urls()
        if url.isLocalFile() and url.toLocalFile().lower().endswith(".pdf")
    ]


def _extract_windows_pdf_attachments(mime_data: QMimeData) -> list[Path]:
    names = _windows_attachment_names(mime_data)
    if not names:
        return []

    MAIL_DROP_DIR.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for index, name in enumerate(names):
        if not name.lower().endswith(".pdf"):
            continue
        data = _windows_file_contents(mime_data, index)
        if not data:
            continue
        safe_name = _safe_attachment_name(name)
        path = MAIL_DROP_DIR / f"{uuid4().hex}_{safe_name}"
        path.write_bytes(data)
        paths.append(path)
    return paths


def _safe_attachment_name(name: str) -> str:
    filename = PureWindowsPath(name).name
    filename = filename.replace("/", "_").replace("\\", "_").strip()
    return filename or "piece_jointe.pdf"


def _windows_attachment_names(mime_data: QMimeData) -> list[str]:
    descriptor_format = _find_windows_mime_format(mime_data, "FileGroupDescriptorW")
    if descriptor_format:
        return _parse_file_group_descriptor_w(bytes(mime_data.data(descriptor_format)))

    descriptor_format = _find_windows_mime_format(mime_data, "FileGroupDescriptor")
    if descriptor_format:
        return _parse_file_group_descriptor_a(bytes(mime_data.data(descriptor_format)))

    return []


def _find_windows_mime_format(mime_data: QMimeData, value: str, index: int | None = None) -> str | None:
    for fmt in mime_data.formats():
        if f'value="{value}"' not in fmt:
            continue
        if index is not None and f"index={index}" not in fmt:
            continue
        return fmt
    return None


def _windows_file_contents(mime_data: QMimeData, index: int) -> bytes:
    content_format = _find_windows_mime_format(mime_data, "FileContents", index)
    if content_format is None and index == 0:
        content_format = _find_windows_mime_format(mime_data, "FileContents")
    if content_format is None:
        return b""
    return bytes(mime_data.data(content_format))


def _parse_file_group_descriptor_w(data: bytes) -> list[str]:
    return _parse_file_group_descriptor(data, descriptor_size=592, name_offset=72, name_size=520, encoding="utf-16le")


def _parse_file_group_descriptor_a(data: bytes) -> list[str]:
    return _parse_file_group_descriptor(data, descriptor_size=332, name_offset=72, name_size=260, encoding="mbcs")


def _parse_file_group_descriptor(
    data: bytes,
    descriptor_size: int,
    name_offset: int,
    name_size: int,
    encoding: str,
) -> list[str]:
    if len(data) < 4:
        return []
    count = int.from_bytes(data[:4], "little", signed=False)
    names: list[str] = []
    for index in range(count):
        start = 4 + index * descriptor_size + name_offset
        end = start + name_size
        if end > len(data):
            break
        raw_name = data[start:end]
        if encoding == "utf-16le":
            terminator = raw_name.find(b"\x00\x00")
            if terminator != -1:
                terminator += terminator % 2
                raw_name = raw_name[:terminator]
        else:
            raw_name = raw_name.split(b"\x00", 1)[0]
        try:
            name = raw_name.decode(encoding, errors="ignore").strip("\x00").strip()
        except LookupError:
            name = raw_name.decode("latin1", errors="ignore").strip("\x00").strip()
        if name:
            names.append(name)
    return names


class DropZone(QWidget):
    pdfs_dropped = Signal(list)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event) -> None:
        if has_pdf_mime(event.mimeData()):
            event.acceptProposedAction()
            return
        super().dragEnterEvent(event)

    def dropEvent(self, event) -> None:
        pdfs = pdf_paths_from_mime(event.mimeData())
        if pdfs:
            self.pdfs_dropped.emit(pdfs)
            event.acceptProposedAction()


class PageCard(QFrame):
    selected = Signal(int, object)
    delete_requested = Signal(int)
    delete_selection_requested = Signal()
    delete_all_requested = Signal()

    def __init__(
        self,
        item: PageItem,
        index: int,
        is_selected: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.item = item
        self.index = index
        self._press_pos: Optional[QPoint] = None
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        grip = QLabel("::::")
        grip.setAlignment(Qt.AlignmentFlag.AlignCenter)
        grip.setCursor(Qt.CursorShape.OpenHandCursor)
        grip.setToolTip("Glisser pour deplacer")
        grip.setFixedHeight(18)
        grip.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        grip.setStyleSheet(
            """
            QLabel {
                color: #111827;
                background: rgba(255, 255, 255, 130);
                border-radius: 4px;
                font-weight: 700;
                letter-spacing: 0;
            }
            """
        )
        layout.addWidget(grip)

        self.image = QLabel()
        self.base_pixmap = QPixmap(str(item.thumbnail_path))
        self.image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        image_size = self.base_pixmap.size()
        if image_size.isEmpty():
            image_size = QSize(140, 198)
        self.image.setFixedSize(image_size)
        self.image.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        layout.addWidget(self.image)

        title = QLabel(item.label)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setWordWrap(True)
        title.setToolTip(item.display_name)
        title.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        layout.addWidget(title)
        self._set_selected(is_selected)

    def _set_selected(self, is_selected: bool) -> None:
        outline = "#ffffff" if is_selected else self.item.source.color
        background = self._card_background(is_selected)
        self.setStyleSheet(
            f"""
            PageCard {{
                background: {background};
                border: 3px solid {outline};
                border-radius: 6px;
            }}
            PageCard:hover {{
                border: 4px solid #ffffff;
            }}
            PageCard QLabel {{
                color: #172033;
                background: transparent;
            }}
            """
        )
        self.image.setPixmap(self._tinted_pixmap() if is_selected else self.base_pixmap)

    def _card_background(self, is_selected: bool) -> str:
        color = QColor(self.item.source.color)
        alpha = 95 if is_selected else 45
        return f"rgba({color.red()}, {color.green()}, {color.blue()}, {alpha})"

    def _tinted_pixmap(self) -> QPixmap:
        tinted = QPixmap(self.base_pixmap)
        painter = QPainter(tinted)
        color = QColor(self.item.source.color)
        color.setAlpha(85)
        painter.fillRect(tinted.rect(), color)
        painter.end()
        return tinted

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.selected.emit(self.index, event.modifiers())
            self.setFocus()
            self._press_pos = event.position().toPoint()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if not (event.buttons() & Qt.MouseButton.LeftButton) or self._press_pos is None:
            return
        if (event.position().toPoint() - self._press_pos).manhattanLength() < 10:
            return

        drag = QDrag(self)
        mime = QMimeData()
        parent = self.parent()
        selected = [self.index]
        while parent:
            if hasattr(parent, "selected_indexes"):
                selected = parent.selected_indexes()
                break
            parent = parent.parent()
        if self.index not in selected:
            selected = [self.index]
        mime.setData(PAGE_MIME, QByteArray(",".join(str(index) for index in selected).encode("utf-8")))
        drag.setMimeData(mime)
        drag.setPixmap(self.grab())
        drag.exec(Qt.DropAction.MoveAction)
        self.setCursor(Qt.CursorShape.OpenHandCursor)

    def mouseReleaseEvent(self, event) -> None:
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        super().mouseReleaseEvent(event)

    def contextMenuEvent(self, event) -> None:
        parent = self.parent()
        selected = [self.index]
        while parent:
            if hasattr(parent, "selected_indexes"):
                selected = parent.selected_indexes()
                break
            parent = parent.parent()
        if self.index not in selected:
            self.selected.emit(self.index, Qt.KeyboardModifier.NoModifier)
            selected = [self.index]

        menu = QMenu(self)
        delete_action = QAction("Supprimer cette page", self)
        delete_action.triggered.connect(lambda: self.delete_requested.emit(self.index))
        menu.addAction(delete_action)
        selected_count = len(selected)
        if selected_count > 1:
            selection_action = QAction(f"Supprimer la selection ({selected_count})", self)
            selection_action.triggered.connect(self.delete_selection_requested)
            menu.addAction(selection_action)
        menu.addSeparator()
        delete_all_action = QAction("Supprimer toutes les pages", self)
        delete_all_action.triggered.connect(self.delete_all_requested)
        menu.addAction(delete_all_action)
        menu.exec(event.globalPos())

    def keyPressEvent(self, event) -> None:
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            parent = self.parent()
            selected_count = 1
            while parent:
                if hasattr(parent, "selected_indexes"):
                    selected_count = len(parent.selected_indexes())
                    break
                parent = parent.parent()
            if selected_count > 1:
                self.delete_selection_requested.emit()
            else:
                self.delete_requested.emit(self.index)
            event.accept()
            return
        super().keyPressEvent(event)


class InsertSlot(QFrame):
    separator_requested = Signal(int)
    page_dropped = Signal(list, int)

    def __init__(self, index: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.index = index
        self.setAcceptDrops(True)
        self.setFixedSize(56, 250)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)
        self.drop_hint = QLabel("I")
        self.drop_hint.setObjectName("dropHint")
        self.drop_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_hint.setFixedHeight(132)
        self.drop_hint.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        layout.addWidget(self.drop_hint)
        layout.addStretch()
        self.button = QPushButton("+")
        self.button.setFixedSize(36, 36)
        self.button.setToolTip("Ajouter un separateur")
        self.button.clicked.connect(lambda: self.separator_requested.emit(self.index))
        layout.addWidget(self.button, alignment=Qt.AlignmentFlag.AlignCenter)
        self.action_hint = QLabel("")
        self.action_hint.setObjectName("actionHint")
        self.action_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.action_hint.setFixedHeight(28)
        self.action_hint.setWordWrap(True)
        self.action_hint.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        layout.addWidget(self.action_hint)
        self._set_active(False)

    def _set_active(self, active: bool) -> None:
        border = "#facc15" if active else "#475569"
        background = "rgba(250, 204, 21, 95)" if active else "rgba(148, 163, 184, 35)"
        hint_background = "#facc15" if active else "#64748b"
        hint_color = "#111827" if active else "#cbd5e1"
        self.action_hint.setText("DEPOSER ICI" if active else "")
        self.setStyleSheet(
            f"""
            InsertSlot {{
                border: 2px dashed {border};
                border-radius: 8px;
                background: {background};
            }}
            InsertSlot:hover {{
                border-color: #93c5fd;
                background: rgba(59, 130, 246, 55);
            }}
            InsertSlot QLabel#actionHint {{
                color: {hint_color};
                background: transparent;
                font-size: 9px;
                font-weight: 800;
            }}
            InsertSlot QLabel#dropHint {{
                color: {hint_background};
                background: transparent;
                font-size: 64px;
                font-weight: 900;
            }}
            QPushButton {{
                border-radius: 18px;
                background: #3b82f6;
                color: #ffffff;
                font-weight: bold;
                font-size: 16px;
            }}
            """
        )

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasFormat(PAGE_MIME):
            self._set_active(True)
            event.acceptProposedAction()

    def dragMoveEvent(self, event) -> None:
        if event.mimeData().hasFormat(PAGE_MIME):
            self._set_active(True)
            event.acceptProposedAction()

    def dragLeaveEvent(self, event) -> None:
        self._set_active(False)
        super().dragLeaveEvent(event)

    def dropEvent(self, event) -> None:
        self._set_active(False)
        raw = bytes(event.mimeData().data(PAGE_MIME)).decode("utf-8")
        source_indexes = [int(index) for index in raw.split(",") if index]
        self.page_dropped.emit(source_indexes, self.index)
        event.acceptProposedAction()


class PageBoard(DropZone):
    move_page_requested = Signal(list, int)
    separator_requested = Signal(int)
    delete_pages_requested = Signal(list)
    delete_all_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.pages: list[PageItem] = []
        self.selected_indices: set[int] = set()
        self.anchor_index: int | None = None
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setAcceptDrops(True)
        self.content = QWidget()
        self.grid = QGridLayout(self.content)
        self.grid.setContentsMargins(14, 14, 14, 14)
        self.grid.setSpacing(8)
        self.scroll.setWidget(self.content)
        root.addWidget(self.scroll)

    def set_pages(self, pages: list[PageItem]) -> None:
        self.pages = pages
        self.selected_indices = {index for index in self.selected_indices if index < len(pages)}
        if self.anchor_index is not None and self.anchor_index >= len(pages):
            self.anchor_index = max(self.selected_indices) if self.selected_indices else None

        while self.grid.count():
            child = self.grid.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if not pages:
            label = QLabel("Importez ou glissez des PDF ici")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("font-size: 18px; color: #cbd5e1; background: transparent;")
            self.grid.addWidget(label, 0, 0)
            return

        columns = 3
        visual_index = 0
        for page_index, page in enumerate(pages):
            slot = InsertSlot(page_index)
            slot.separator_requested.connect(self.separator_requested)
            slot.page_dropped.connect(self.move_page_requested)
            row = visual_index // (columns * 2)
            col = visual_index % (columns * 2)
            self.grid.addWidget(slot, row, col)
            visual_index += 1

            card = PageCard(page, page_index, page_index in self.selected_indices)
            card.selected.connect(self.select_page)
            card.delete_requested.connect(lambda index: self.delete_pages_requested.emit([index]))
            card.delete_selection_requested.connect(self.delete_selection)
            card.delete_all_requested.connect(self.delete_all_requested)
            row = visual_index // (columns * 2)
            col = visual_index % (columns * 2)
            self.grid.addWidget(card, row, col)
            visual_index += 1

        slot = InsertSlot(len(pages))
        slot.separator_requested.connect(self.separator_requested)
        slot.page_dropped.connect(self.move_page_requested)
        row = visual_index // (columns * 2)
        col = visual_index % (columns * 2)
        self.grid.addWidget(slot, row, col)

    def select_page(self, index: int, modifiers) -> None:
        if modifiers & Qt.KeyboardModifier.ShiftModifier and self.anchor_index is not None:
            start = min(self.anchor_index, index)
            end = max(self.anchor_index, index)
            self.selected_indices = set(range(start, end + 1))
        elif modifiers & Qt.KeyboardModifier.ControlModifier:
            if index in self.selected_indices:
                self.selected_indices.remove(index)
            else:
                self.selected_indices.add(index)
                self.anchor_index = index
        else:
            self.selected_indices = {index}
            self.anchor_index = index
        self.setFocus()
        for item_index in range(self.grid.count()):
            widget = self.grid.itemAt(item_index).widget()
            if isinstance(widget, PageCard):
                widget._set_selected(widget.index in self.selected_indices)

    def selected_indexes(self) -> list[int]:
        return sorted(self.selected_indices)

    def clear_selection(self) -> None:
        self.selected_indices.clear()
        self.anchor_index = None

    def delete_selection(self) -> None:
        if self.selected_indices:
            self.delete_pages_requested.emit(self.selected_indexes())

    def keyPressEvent(self, event) -> None:
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            if self.selected_indices:
                self.delete_pages_requested.emit(self.selected_indexes())
                event.accept()
                return
        super().keyPressEvent(event)


class SeparatorDialog(QDialog):
    def __init__(self, options: list[SeparatorOption], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Ajouter un separateur")
        self.resize(460, 520)
        self.options = options
        self.selected: SeparatorOption | None = None
        self.setStyleSheet(
            """
            QDialog {
                background: #111827;
                color: #f9fafb;
                font-family: "Segoe UI", Arial, sans-serif;
            }
            QLineEdit {
                background: #f9fafb;
                color: #111827;
                border: 1px solid #64748b;
                border-radius: 5px;
                padding: 7px;
            }
            QListWidget {
                background: #0f172a;
                color: #f9fafb;
                border: 1px solid #374151;
                border-radius: 5px;
            }
            QListWidget::item {
                padding: 8px;
            }
            QListWidget::item:selected {
                background: #2563eb;
                color: #ffffff;
            }
            QPushButton {
                background: #2563eb;
                color: #ffffff;
                border: none;
                border-radius: 5px;
                padding: 8px 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #1d4ed8;
            }
            """
        )

        layout = QVBoxLayout(self)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Rechercher...")
        self.search.textChanged.connect(self._refresh)
        layout.addWidget(self.search)

        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self._choose_item)
        layout.addWidget(self.list_widget)

        buttons = QHBoxLayout()
        cancel = QPushButton("Annuler")
        cancel.clicked.connect(self.reject)
        choose = QPushButton("Ajouter")
        choose.clicked.connect(self._choose_current)
        buttons.addWidget(cancel)
        buttons.addStretch()
        buttons.addWidget(choose)
        layout.addLayout(buttons)
        self._refresh()

    def _refresh(self) -> None:
        query = self.search.text().strip().lower()
        self.list_widget.clear()
        for option in self.options:
            if query and query not in option.name.lower():
                continue
            item = QListWidgetItem(f"{option.name} ({option.page_count} page(s))")
            item.setData(Qt.ItemDataRole.UserRole, option)
            if option.preview_path:
                item.setIcon(QIcon(str(option.preview_path)))
            self.list_widget.addItem(item)

    def _choose_current(self) -> None:
        item = self.list_widget.currentItem()
        if item:
            self._choose_item(item)

    def _choose_item(self, item: QListWidgetItem) -> None:
        self.selected = item.data(Qt.ItemDataRole.UserRole)
        self.accept()


class DraggableFile(QFrame):
    def __init__(self, path: Path, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.path = path
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.setStyleSheet(
            """
            DraggableFile {
                border: 2px dashed #60a5fa;
                border-radius: 8px;
                background: #1e293b;
            }
            DraggableFile QLabel {
                color: #f9fafb;
                background: transparent;
            }
            """
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        label = QLabel(path.name)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setWordWrap(True)
        layout.addWidget(label)

    def mouseMoveEvent(self, event) -> None:
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        drag = QDrag(self)
        mime = QMimeData()
        mime.setUrls([QUrl.fromLocalFile(str(self.path.resolve()))])
        drag.setMimeData(mime)
        drag.exec(Qt.DropAction.CopyAction)
