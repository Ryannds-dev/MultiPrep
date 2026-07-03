from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QByteArray, QMimeData, QObject, QPoint, QRunnable, Qt, QThreadPool, QTimer, Signal
from PySide6.QtGui import QDrag, QKeySequence
from PySide6.QtWidgets import QAbstractItemView, QListView, QListWidget, QListWidgetItem, QWidget

from multiprep.models.page_model import PageItem
from multiprep.services.drop_service import file_paths_from_mime, has_supported_file_mime
from multiprep.services.thumbnail_service import ensure_page_thumbnails
from multiprep.ui.page_card_delegate import CARD_SIZE, PageCardDelegate
from multiprep.ui.page_thumbnail import PagePlaceholderWidget


PAGE_DRAG_MIME = "application/x-multiprep-page-items"
PAGE_ROLE = Qt.ItemDataRole.UserRole
PLACEHOLDER_ROLE = Qt.ItemDataRole.UserRole + 1
ITEM_SIZE = CARD_SIZE


class _ThumbnailSignals(QObject):
    finished = Signal(int, list)


class _ThumbnailWorker(QRunnable):
    def __init__(self, generation: int, rows: list[int], pages: list[PageItem]) -> None:
        super().__init__()
        self.generation = generation
        self.rows = rows
        self.pages = pages
        self.signals = _ThumbnailSignals()

    def run(self) -> None:
        try:
            ensure_page_thumbnails(self.pages)
        finally:
            self.signals.finished.emit(self.generation, self.rows)


class PageGridListWidget(QListWidget):
    pdfs_dropped = Signal(list)
    order_changed = Signal(list)
    delete_selected_requested = Signal()
    paste_requested = Signal()
    browser_drop_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._drag_original_pages: list[PageItem] | None = None
        self._drag_pages: list[PageItem] = []
        self._placeholder_item: QListWidgetItem | None = None
        self._render_generation = 0
        self._pending_widget_rows: list[int] = []
        self._thumbnail_workers: set[_ThumbnailWorker] = set()
        self._configure()

    def set_pages(self, pages: list[PageItem]) -> None:
        self._rebuild_items(pages)

    def get_ordered_pages(self) -> list[PageItem]:
        pages: list[PageItem] = []
        for row in range(self.count()):
            item = self.item(row)
            if not item.data(PLACEHOLDER_ROLE):
                pages.append(item.data(PAGE_ROLE))
        return pages

    def dragEnterEvent(self, event) -> None:
        formats = {fmt.lower() for fmt in event.mimeData().formats()}
        browser_virtual_file = (
            "application/x-qt-image" in formats
            or "chromium/x-renderer-taint" in formats
            or "filegroupdescriptorw" in formats
            or "filecontents" in formats
        )
        if browser_virtual_file and not file_paths_from_mime(event.mimeData()):
            self.browser_drop_requested.emit()
        if has_supported_file_mime(event.mimeData()) or event.mimeData().hasFormat(PAGE_DRAG_MIME):
            event.acceptProposedAction()
            return
        super().dragEnterEvent(event)

    def dragMoveEvent(self, event) -> None:
        if has_supported_file_mime(event.mimeData()):
            event.acceptProposedAction()
            return
        if event.mimeData().hasFormat(PAGE_DRAG_MIME):
            self._move_placeholder(self._target_index_at(event.position().toPoint()))
            event.acceptProposedAction()
            return
        super().dragMoveEvent(event)

    def dropEvent(self, event) -> None:
        files = file_paths_from_mime(event.mimeData())
        if files:
            self.pdfs_dropped.emit(files)
            event.acceptProposedAction()
            return
        if event.mimeData().hasFormat(PAGE_DRAG_MIME):
            self._commit_placeholder_drop()
            event.acceptProposedAction()
            return
        super().dropEvent(event)
        self.order_changed.emit(self.get_ordered_pages())

    def startDrag(self, supported_actions) -> None:
        rows = self._selected_rows()
        if not rows:
            return
        self._drag_original_pages = self.get_ordered_pages()
        self._drag_pages = [self._drag_original_pages[row] for row in rows]
        self._remove_rows(rows)
        self._insert_placeholder(min(rows))

        drag = QDrag(self)
        mime = QMimeData()
        mime.setData(PAGE_DRAG_MIME, QByteArray(b"pages"))
        drag.setMimeData(mime)
        self._set_drag_preview(drag)
        if drag.exec(Qt.DropAction.MoveAction) != Qt.DropAction.MoveAction:
            self._restore_cancelled_drag()

    def keyPressEvent(self, event) -> None:
        if event.matches(QKeySequence.StandardKey.Paste):
            self.paste_requested.emit()
            event.accept()
            return
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace) and self.selectedItems():
            self.delete_selected_requested.emit()
            event.accept()
            return
        super().keyPressEvent(event)

    def _configure(self) -> None:
        self.setViewMode(QListView.ViewMode.IconMode)
        self.setResizeMode(QListView.ResizeMode.Adjust)
        self.setFlow(QListView.Flow.LeftToRight)
        self.setWrapping(True)
        self.setMovement(QListView.Movement.Snap)
        self.setUniformItemSizes(True)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setSpacing(12)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.setItemDelegate(PageCardDelegate(self))

    def _selected_rows(self) -> list[int]:
        return sorted(self.row(item) for item in self.selectedItems() if not item.data(PLACEHOLDER_ROLE))

    def _add_page_item(self, page: PageItem) -> QListWidgetItem:
        item = QListWidgetItem()
        item.setData(PAGE_ROLE, page)
        item.setData(PLACEHOLDER_ROLE, False)
        item.setSizeHint(ITEM_SIZE)
        self.addItem(item)
        return item

    def _insert_placeholder(self, index: int) -> None:
        item = QListWidgetItem()
        item.setData(PLACEHOLDER_ROLE, True)
        item.setSizeHint(ITEM_SIZE)
        self.insertItem(index, item)
        self.setItemWidget(item, PagePlaceholderWidget(len(self._drag_pages)))
        self._placeholder_item = item

    def _remove_rows(self, rows: list[int]) -> None:
        def remove() -> None:
            for row in reversed(rows):
                item = self.item(row)
                if item is None:
                    continue
                widget = self.itemWidget(item)
                if widget is not None:
                    self.removeItemWidget(item)
                    widget.deleteLater()
                self.takeItem(row)

        self._batch_update(remove)

    def _target_index_at(self, position: QPoint) -> int:
        item = self.itemAt(position)
        if item is None:
            return self.count() - (1 if self._placeholder_item else 0)
        index = self.row(item) + (1 if position.x() > self.visualItemRect(item).center().x() else 0)
        if self._placeholder_item is not None and index > self.row(self._placeholder_item):
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

    def _set_drag_preview(self, drag: QDrag) -> None:
        widget = self.itemWidget(self._placeholder_item) if self._placeholder_item else None
        if not widget:
            return
        pixmap = widget.grab()
        drag.setPixmap(pixmap)
        drag.setHotSpot(QPoint(pixmap.width() // 2, pixmap.height() // 2))

    def _rebuild_items(self, pages: list[PageItem]) -> None:
        self._render_generation += 1
        generation = self._render_generation

        def render() -> None:
            self.clear()
            for page in pages:
                self._add_page_item(page)

        self._batch_update(render)
        self._pending_widget_rows = list(range(len(pages)))
        QTimer.singleShot(0, lambda: self._pump_thumbnail_workers(generation))

    def append_pages(self, pages: list[PageItem]) -> None:
        if not pages:
            return
        self._render_generation += 1
        generation = self._render_generation
        first_row = self.count()
        for page in pages:
            self._add_page_item(page)
        self._pending_widget_rows = list(range(first_row, self.count()))
        QTimer.singleShot(0, lambda: self._pump_thumbnail_workers(generation))

    def _pump_thumbnail_workers(self, generation: int) -> None:
        if generation != self._render_generation:
            return
        while self._pending_widget_rows and len(self._thumbnail_workers) < 4:
            rows = self._pending_widget_rows[:8]
            del self._pending_widget_rows[:8]
            pages = [
                self.item(row).data(PAGE_ROLE)
                for row in rows
                if self.item(row) is not None and not self.item(row).data(PLACEHOLDER_ROLE)
            ]
            worker = _ThumbnailWorker(generation, rows, pages)
            worker.signals.finished.connect(
                lambda finished_generation, finished_rows, current=worker:
                    self._finish_thumbnail_batch(current, finished_generation, finished_rows)
            )
            self._thumbnail_workers.add(worker)
            QThreadPool.globalInstance().start(worker)

    def _finish_thumbnail_batch(
        self,
        worker: _ThumbnailWorker,
        generation: int,
        rows: list[int],
    ) -> None:
        self._thumbnail_workers.discard(worker)
        if generation != self._render_generation:
            QTimer.singleShot(
                0,
                lambda: self._pump_thumbnail_workers(self._render_generation),
            )
            return
        self.viewport().update()
        if self._pending_widget_rows:
            QTimer.singleShot(0, lambda: self._pump_thumbnail_workers(generation))

    def _batch_update(self, callback: Callable[[], None]) -> None:
        previous_updates = self.updatesEnabled()
        previous_viewport_updates = self.viewport().updatesEnabled()
        previous_signals = self.blockSignals(True)
        self.setUpdatesEnabled(False)
        self.viewport().setUpdatesEnabled(False)
        try:
            callback()
        finally:
            self.viewport().setUpdatesEnabled(previous_viewport_updates)
            self.setUpdatesEnabled(previous_updates)
            self.blockSignals(previous_signals)
            self.viewport().update()
