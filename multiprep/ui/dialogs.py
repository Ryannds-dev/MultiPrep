from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDrag, QIcon
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from multiprep.models.page_model import SeparatorOption


class SeparatorDialog(QDialog):
    def __init__(self, options: list[SeparatorOption], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Ajouter un separateur")
        self.resize(460, 520)
        self.options = options
        self.selected: SeparatorOption | None = None
        self.setStyleSheet(DIALOG_STYLE)
        self._build()
        self._refresh()

    def _build(self) -> None:
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
        self.setStyleSheet(DRAGGABLE_FILE_STYLE)
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
        mime = self._mime_data()
        drag.setMimeData(mime)
        drag.exec(Qt.DropAction.CopyAction)

    def _mime_data(self):
        from PySide6.QtCore import QMimeData

        mime = QMimeData()
        mime.setUrls([QUrl.fromLocalFile(str(self.path.resolve()))])
        return mime


DIALOG_STYLE = """
QDialog { background: #111827; color: #f9fafb; font-family: "Segoe UI", Arial, sans-serif; }
QLineEdit { background: #f9fafb; color: #111827; border: 1px solid #64748b; border-radius: 5px; padding: 7px; }
QListWidget { background: #0f172a; color: #f9fafb; border: 1px solid #374151; border-radius: 5px; }
QListWidget::item { padding: 8px; }
QListWidget::item:selected { background: #2563eb; color: #ffffff; }
QPushButton { background: #2563eb; color: #ffffff; border: none; border-radius: 5px; padding: 8px 12px; font-weight: 600; }
QPushButton:hover { background: #1d4ed8; }
"""

DRAGGABLE_FILE_STYLE = """
DraggableFile { border: 2px dashed #60a5fa; border-radius: 8px; background: #1e293b; }
DraggableFile QLabel { color: #f9fafb; background: transparent; }
"""
