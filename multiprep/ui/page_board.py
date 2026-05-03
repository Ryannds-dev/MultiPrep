from __future__ import annotations

from PySide6.QtCore import QPoint, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QListWidgetItem, QMenu, QVBoxLayout, QWidget

from multiprep.models.page_model import PageItem
from multiprep.ui.page_grid_list import PLACEHOLDER_ROLE, PageGridListWidget
from multiprep.ui.page_thumbnail import PageThumbnailWidget


class PageBoard(QWidget):
    order_changed = Signal(list)
    separator_requested = Signal(int)
    delete_pages_requested = Signal(list)
    delete_all_requested = Signal()
    pdfs_dropped = Signal(list)
    paste_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.pages: list[PageItem] = []
        self.setAcceptDrops(True)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        self.list_widget = PageGridListWidget()
        self._connect_list()
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

    def _connect_list(self) -> None:
        self.list_widget.pdfs_dropped.connect(self.pdfs_dropped.emit)
        self.list_widget.order_changed.connect(self._apply_order)
        self.list_widget.delete_selected_requested.connect(self.delete_selection)
        self.list_widget.paste_requested.connect(self.paste_requested.emit)
        self.list_widget.itemSelectionChanged.connect(self._sync_selection_styles)
        self.list_widget.customContextMenuRequested.connect(self._open_context_menu)

    def _apply_order(self, pages: list[PageItem]) -> None:
        self.pages = pages
        self.list_widget.set_pages(pages)
        self.order_changed.emit(pages)

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
        paste_action = QAction("Coller", self)
        paste_action.triggered.connect(lambda _checked=False: self.paste_requested.emit())
        menu.addAction(paste_action)
        menu.addSeparator()
        self._add_page_actions(menu, item)
        menu.exec(self.list_widget.viewport().mapToGlobal(position))

    def _add_page_actions(self, menu: QMenu, item: QListWidgetItem | None) -> None:
        if item:
            selected_count = len(self.list_widget.selectedItems())
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
        delete_all_action.triggered.connect(lambda _checked=False: self.delete_all_requested.emit())
        menu.addAction(delete_all_action)
