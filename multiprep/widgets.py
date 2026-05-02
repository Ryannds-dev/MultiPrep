from __future__ import annotations

import shutil
import tempfile
from pathlib import PureWindowsPath
from pathlib import Path
from uuid import uuid4

from PySide6.QtCore import QByteArray, QMimeData, QPoint, QSize, Qt, QUrl, Signal
from PySide6.QtGui import QAction, QColor, QDrag, QIcon, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListView,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .models import PageItem, SeparatorOption


FILE_MIME = "text/uri-list"
PAGE_DRAG_MIME = "application/x-multiprep-page-items"
PAGE_ROLE = Qt.ItemDataRole.UserRole
PLACEHOLDER_ROLE = Qt.ItemDataRole.UserRole + 1
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

        title = QLabel(f"{number}. {item.source.path.name}")
        if item.is_separator:
            title.setText(f"{number}. Separateur - {item.source.path.stem}")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setWordWrap(True)
        title.setToolTip(item.display_name)
        layout.addWidget(title)

    def set_selected(self, selected: bool) -> None:
        self.setStyleSheet(self._style(selected))

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
            color: #172033;
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


class PageGridListWidget(QListWidget):
    pdfs_dropped = Signal(list)
    order_changed = Signal(list)
    delete_selected_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._drag_original_pages: list[PageItem] | None = None
        self._drag_pages: list[PageItem] = []
        self._placeholder_item: QListWidgetItem | None = None
        self.setViewMode(QListView.ViewMode.IconMode)
        self.setResizeMode(QListView.ResizeMode.Adjust)
        self.setFlow(QListView.Flow.LeftToRight)
        self.setWrapping(True)
        self.setMovement(QListView.Movement.Snap)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setSpacing(12)
        self.setUniformItemSizes(False)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

    def set_pages(self, pages: list[PageItem]) -> None:
        self.clear()
        for index, page in enumerate(pages):
            self._add_page_item(page, index + 1)

    def dragEnterEvent(self, event) -> None:
        if has_pdf_mime(event.mimeData()):
            event.acceptProposedAction()
            return
        if event.mimeData().hasFormat(PAGE_DRAG_MIME):
            event.acceptProposedAction()
            return
        super().dragEnterEvent(event)

    def dragMoveEvent(self, event) -> None:
        if has_pdf_mime(event.mimeData()):
            event.acceptProposedAction()
            return
        if event.mimeData().hasFormat(PAGE_DRAG_MIME):
            self._move_placeholder(self._target_index_at(event.position().toPoint()))
            event.acceptProposedAction()
            return
        super().dragMoveEvent(event)

    def dropEvent(self, event) -> None:
        pdfs = pdf_paths_from_mime(event.mimeData())
        if pdfs:
            self.pdfs_dropped.emit(pdfs)
            event.acceptProposedAction()
            return
        if event.mimeData().hasFormat(PAGE_DRAG_MIME):
            self._commit_placeholder_drop()
            event.acceptProposedAction()
            return
        super().dropEvent(event)
        self.order_changed.emit(self.get_ordered_pages())

    def startDrag(self, supported_actions) -> None:
        selected_rows = self._selected_rows()
        if not selected_rows:
            return

        self._drag_original_pages = self.get_ordered_pages()
        self._drag_pages = [self._drag_original_pages[row] for row in selected_rows]
        remaining = [
            page
            for index, page in enumerate(self._drag_original_pages)
            if index not in set(selected_rows)
        ]
        placeholder_index = min(selected_rows)
        self._render_with_placeholder(remaining, placeholder_index)

        drag = QDrag(self)
        mime = QMimeData()
        mime.setData(PAGE_DRAG_MIME, QByteArray(b"pages"))
        drag.setMimeData(mime)
        widget = self.itemWidget(self._placeholder_item) if self._placeholder_item else None
        if widget:
            pixmap = widget.grab()
            drag.setPixmap(pixmap)
            drag.setHotSpot(QPoint(pixmap.width() // 2, pixmap.height() // 2))

        result = drag.exec(Qt.DropAction.MoveAction)
        if result != Qt.DropAction.MoveAction and self._drag_original_pages is not None:
            self._restore_cancelled_drag()

    def keyPressEvent(self, event) -> None:
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace) and self.selectedItems():
            self.delete_selected_requested.emit()
            event.accept()
            return
        super().keyPressEvent(event)

    def get_ordered_pages(self) -> list[PageItem]:
        pages: list[PageItem] = []
        for row in range(self.count()):
            item = self.item(row)
            if item.data(PLACEHOLDER_ROLE):
                continue
            pages.append(item.data(PAGE_ROLE))
        return pages

    def _selected_rows(self) -> list[int]:
        return sorted(self.row(item) for item in self.selectedItems() if not item.data(PLACEHOLDER_ROLE))

    def _add_page_item(self, page: PageItem, number: int) -> QListWidgetItem:
        item = QListWidgetItem()
        item.setData(PAGE_ROLE, page)
        item.setData(PLACEHOLDER_ROLE, False)
        item.setSizeHint(QSize(226, 334))
        self.addItem(item)
        self.setItemWidget(item, PageThumbnailWidget(page, number))
        return item

    def _insert_placeholder(self, index: int) -> None:
        item = QListWidgetItem()
        item.setData(PLACEHOLDER_ROLE, True)
        item.setSizeHint(QSize(226, 334))
        self.insertItem(index, item)
        self.setItemWidget(item, PagePlaceholderWidget(len(self._drag_pages)))
        self._placeholder_item = item

    def _render_with_placeholder(self, pages: list[PageItem], placeholder_index: int) -> None:
        self.clear()
        placeholder_index = max(0, min(placeholder_index, len(pages)))
        for index in range(len(pages) + 1):
            if index == placeholder_index:
                self._insert_placeholder(index)
            if index < len(pages):
                self._add_page_item(pages[index], index + 1)

    def _target_index_at(self, position: QPoint) -> int:
        item = self.itemAt(position)
        if item is None:
            return self.count() - (1 if self._placeholder_item else 0)
        index = self.row(item)
        rect = self.visualItemRect(item)
        if position.x() > rect.center().x():
            index += 1
        if self._placeholder_item is not None:
            placeholder_index = self.row(self._placeholder_item)
            if index > placeholder_index:
                index -= 1
        return max(0, min(index, self.count() - 1))

    def _move_placeholder(self, target_index: int) -> None:
        if self._placeholder_item is None:
            return
        current_index = self.row(self._placeholder_item)
        target_index = max(0, min(target_index, self.count() - 1))
        if current_index == target_index:
            return
        item = self.takeItem(current_index)
        self.insertItem(target_index, item)
        self.setItemWidget(item, PagePlaceholderWidget(len(self._drag_pages)))
        self._placeholder_item = item

    def _commit_placeholder_drop(self) -> None:
        if self._placeholder_item is None:
            self._restore_cancelled_drag()
            return
        placeholder_index = self.row(self._placeholder_item)
        pages = self.get_ordered_pages()
        for offset, page in enumerate(self._drag_pages):
            pages.insert(placeholder_index + offset, page)
        self._clear_drag_state()
        self.set_pages(pages)
        self.order_changed.emit(pages)

    def _restore_cancelled_drag(self) -> None:
        pages = self._drag_original_pages or []
        self._clear_drag_state()
        self.set_pages(pages)

    def _clear_drag_state(self) -> None:
        self._drag_original_pages = None
        self._drag_pages = []
        self._placeholder_item = None


class PageBoard(QWidget):
    order_changed = Signal(list)
    separator_requested = Signal(int)
    delete_pages_requested = Signal(list)
    delete_all_requested = Signal()
    pdfs_dropped = Signal(list)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.pages: list[PageItem] = []
        self.setAcceptDrops(True)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        self.list_widget = PageGridListWidget()
        self.list_widget.pdfs_dropped.connect(self.pdfs_dropped)
        self.list_widget.order_changed.connect(self._apply_order)
        self.list_widget.delete_selected_requested.connect(self.delete_selection)
        self.list_widget.itemSelectionChanged.connect(self._sync_selection_styles)
        self.list_widget.customContextMenuRequested.connect(self._open_context_menu)
        root.addWidget(self.list_widget)

    def set_pages(self, pages: list[PageItem]) -> None:
        self.pages = pages
        self.list_widget.set_pages(pages)

    def selected_indexes(self) -> list[int]:
        return sorted(self.list_widget.row(item) for item in self.list_widget.selectedItems())

    def clear_selection(self) -> None:
        self.list_widget.clearSelection()

    def delete_selection(self) -> None:
        if self.list_widget.selectedItems():
            self.delete_pages_requested.emit(self.selected_indexes())

    def get_ordered_pages(self) -> list[PageItem]:
        return self.list_widget.get_ordered_pages()

    def _apply_order(self, pages: list[PageItem]) -> None:
        self.pages = pages
        self._refresh_numbers()
        self.order_changed.emit(pages)

    def _refresh_numbers(self) -> None:
        self.list_widget.set_pages(self.list_widget.get_ordered_pages())
        self._sync_selection_styles()

    def _sync_selection_styles(self) -> None:
        for row in range(self.list_widget.count()):
            item = self.list_widget.item(row)
            if item.data(PLACEHOLDER_ROLE):
                continue
            widget = self.list_widget.itemWidget(item)
            if isinstance(widget, PageThumbnailWidget):
                widget.set_selected(item.isSelected())

    def _open_context_menu(self, position: QPoint) -> None:
        item = self.list_widget.itemAt(position)
        if item and not item.isSelected():
            self.list_widget.clearSelection()
            item.setSelected(True)

        menu = QMenu(self)
        selected_count = len(self.list_widget.selectedItems())
        if item:
            delete_action = QAction(
                f"Supprimer la selection ({selected_count})" if selected_count > 1 else "Supprimer cette page",
                self,
            )
            delete_action.triggered.connect(self.delete_selection)
            menu.addAction(delete_action)

            row = self.list_widget.row(item)
            before_action = QAction("Ajouter un separateur avant", self)
            before_action.triggered.connect(lambda: self.separator_requested.emit(row))
            after_action = QAction("Ajouter un separateur apres", self)
            after_action.triggered.connect(lambda: self.separator_requested.emit(row + 1))
            menu.addAction(before_action)
            menu.addAction(after_action)

        end_separator = QAction("Ajouter un separateur a la fin", self)
        end_separator.triggered.connect(lambda: self.separator_requested.emit(self.list_widget.count()))
        menu.addAction(end_separator)
        menu.addSeparator()
        delete_all_action = QAction("Supprimer toutes les pages", self)
        delete_all_action.triggered.connect(self.delete_all_requested)
        menu.addAction(delete_all_action)
        menu.exec(self.list_widget.viewport().mapToGlobal(position))


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
