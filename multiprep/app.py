from __future__ import annotations

import re
import sys
import unicodedata
import ctypes
from colorsys import hls_to_rgb
from datetime import date
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QStackedWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from .models import PageItem, SourceDocument
from .pdf_service import PdfService
from .settings import load_settings, save_last_date
from .widgets import (
    DraggableFile,
    PageBoard,
    SeparatorDialog,
    cleanup_mail_drop_dir,
    has_pdf_mime,
    pdf_paths_from_mime,
)


def build_source_colors(count: int = 100) -> list[str]:
    colors: list[str] = []
    golden_ratio = 0.61803398875
    hue = 0.58
    for index in range(count):
        hue = (hue + golden_ratio) % 1.0
        lightness = 0.74 if index % 2 == 0 else 0.66
        saturation = 0.62 if index % 3 else 0.72
        red, green, blue = hls_to_rgb(hue, lightness, saturation)
        colors.append(f"#{int(red * 255):02x}{int(green * 255):02x}{int(blue * 255):02x}")
    return colors


SOURCE_COLORS = build_source_colors()
APP_ICON_PATH = Path("assets") / "multiprep-logo.ico"


def resource_path(relative_path: Path) -> Path:
    base_path = Path(getattr(sys, "_MEIPASS", Path.cwd()))
    return base_path / relative_path


def set_windows_app_id() -> None:
    if sys.platform != "win32":
        return
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("MultiPrep.MultiPrep")
    except Exception:
        pass


class DateSpin(QWidget):
    class PaddedSpinBox(QSpinBox):
        def __init__(self, digits: int) -> None:
            super().__init__()
            self.digits = digits

        def textFromValue(self, value: int) -> str:
            return f"{value:0{self.digits}d}" if self.digits > 1 else str(value)

    def __init__(self, minimum: int, maximum: int, value: int, width: int, digits: int = 1) -> None:
        super().__init__()
        self.spin = self.PaddedSpinBox(digits)
        self.spin.setRange(minimum, maximum)
        self.spin.setValue(value)
        self.spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.spin.setFixedWidth(width)
        self.spin.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.spin.setKeyboardTracking(False)

        minus = QToolButton()
        minus.setText("-")
        minus.setToolTip("Reduire")
        minus.clicked.connect(lambda: self.spin.stepBy(-1))

        plus = QToolButton()
        plus.setText("+")
        plus.setToolTip("Augmenter")
        plus.clicked.connect(lambda: self.spin.stepBy(1))

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)
        layout.addWidget(minus)
        layout.addWidget(self.spin)
        layout.addWidget(plus)

    def value(self) -> int:
        return self.spin.value()

    def setValue(self, value: int) -> None:
        self.spin.setValue(value)


class MultiPrepWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("MultiPrep")
        self.setWindowIcon(QIcon(str(resource_path(APP_ICON_PATH))))
        self.resize(1180, 760)
        self.setAcceptDrops(True)

        self.pdf_service = PdfService()
        self.sources: list[SourceDocument] = []
        self.pages: list[PageItem] = []
        self.next_source_id = 1
        self.last_output_path: Path | None = None
        self.separator_folder = Path("separateurs")
        self.output_folder = Path("exports")

        settings = load_settings()

        self.stack = QStackedWidget()
        self.editor_page = QWidget()
        self.result_page = QWidget()
        self.stack.addWidget(self.editor_page)
        self.stack.addWidget(self.result_page)
        self.setCentralWidget(self.stack)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Nom")
        self.firstname_edit = QLineEdit()
        self.firstname_edit.setPlaceholderText("Prenom")
        self.day_spin = self._spin(1, 31, settings.last_date.day)
        self.month_spin = self._spin(1, 12, settings.last_date.month)
        self.year_spin = self._spin(1900, 2200, settings.last_date.year)
        self.suffix_check = QCheckBox("P")
        self.suffix_check.setChecked(True)

        self.board = PageBoard()
        self.board.pdfs_dropped.connect(self.add_pdfs)
        self.board.order_changed.connect(self.set_page_order)
        self.board.separator_requested.connect(self.open_separator_dialog)
        self.board.delete_pages_requested.connect(self.delete_pages)
        self.board.delete_all_requested.connect(self.delete_all_pages)
        self.board.paste_requested.connect(self.handle_paste)

        self._build_editor()
        self._build_result_shell()
        self._apply_style()
        self.board.set_pages(self.pages)

    def closeEvent(self, event) -> None:
        self.pdf_service.cleanup()
        cleanup_mail_drop_dir()
        super().closeEvent(event)

    def dragEnterEvent(self, event) -> None:
        if has_pdf_mime(event.mimeData()):
            event.acceptProposedAction()
            return
        super().dragEnterEvent(event)

    def dropEvent(self, event) -> None:
        pdfs = self._pdfs_from_event(event)
        if pdfs:
            self.add_pdfs(pdfs)
            event.acceptProposedAction()
            return
        super().dropEvent(event)

    def keyPressEvent(self, event) -> None:
        if event.matches(QKeySequence.StandardKey.Paste):
            self.handle_paste()
            event.accept()
            return
        super().keyPressEvent(event)

    def _build_editor(self) -> None:
        layout = QVBoxLayout(self.editor_page)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        top = QHBoxLayout()
        import_button = QPushButton("Importer PDF")
        import_button.clicked.connect(self.choose_pdfs)
        generate_button = QPushButton("Generer PDF")
        generate_button.clicked.connect(self.generate_pdf)

        top.addWidget(QLabel("Nom"))
        top.addWidget(self.name_edit, 2)
        top.addWidget(QLabel("Prenom"))
        top.addWidget(self.firstname_edit, 2)
        top.addWidget(QLabel("Date"))
        top.addWidget(self.day_spin)
        top.addWidget(self.month_spin)
        top.addWidget(self.year_spin)
        top.addWidget(QLabel("Suffixe"))
        top.addWidget(self.suffix_check)
        top.addStretch()
        top.addWidget(import_button)
        top.addWidget(generate_button)
        layout.addLayout(top)

        paste_hint = QLabel("Astuce : utilisez Ctrl + V ou clic droit -> coller pour coller une capture du mail")
        paste_hint.setStyleSheet("color: #cbd5e1; font-size: 9pt;")
        layout.addWidget(paste_hint)
        layout.addWidget(self.board, 1)

    def _build_result_shell(self) -> None:
        self.result_layout = QVBoxLayout(self.result_page)
        self.result_layout.setContentsMargins(40, 40, 40, 40)
        self.result_layout.setSpacing(18)

    def _show_result(self, output_path: Path) -> None:
        while self.result_layout.count():
            child = self.result_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                while child.layout().count():
                    item = child.layout().takeAt(0)
                    if item.widget():
                        item.widget().deleteLater()

        title = QLabel("PDF genere")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 28px; font-weight: 700;")
        filename = QLabel(output_path.name)
        filename.setAlignment(Qt.AlignmentFlag.AlignCenter)
        filename.setWordWrap(True)
        hint = QLabel("Glissez ce fichier vers Multigest")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)

        file_zone = DraggableFile(output_path)
        file_zone.setMinimumHeight(120)

        buttons = QHBoxLayout()
        cancel = QPushButton("Annuler")
        cancel.clicked.connect(lambda: self.stack.setCurrentWidget(self.editor_page))
        new_case = QPushButton("Nouveau dossier")
        new_case.clicked.connect(self.reset_case)
        buttons.addWidget(cancel)
        buttons.addStretch()
        buttons.addWidget(new_case)

        self.result_layout.addStretch()
        self.result_layout.addWidget(title)
        self.result_layout.addWidget(filename)
        self.result_layout.addWidget(hint)
        self.result_layout.addWidget(file_zone)
        self.result_layout.addLayout(buttons)
        self.result_layout.addStretch()
        self.stack.setCurrentWidget(self.result_page)

    def _spin(self, minimum: int, maximum: int, value: int) -> DateSpin:
        digits = 2 if maximum <= 31 else 4
        return DateSpin(minimum, maximum, value, 66 if maximum > 99 else 46, digits)

    def choose_pdfs(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Importer des PDF",
            str(Path.home()),
            "PDF (*.pdf)",
        )
        self.add_pdfs([Path(path) for path in paths])

    def add_pdfs(self, paths: list[Path]) -> None:
        for path in paths:
            if not path.exists() or path.suffix.lower() != ".pdf":
                continue
            color = SOURCE_COLORS[(self.next_source_id - 1) % len(SOURCE_COLORS)]
            source = SourceDocument(self.next_source_id, path, color)
            self.next_source_id += 1
            try:
                self.pages.extend(self.pdf_service.document_pages(source))
                self.sources.append(source)
            except Exception as exc:
                QMessageBox.warning(self, "Import impossible", f"{path.name}\n{exc}")
        self.board.set_pages(self.pages)

    def handle_paste(self) -> None:
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()
        if not mime_data.hasImage():
            QMessageBox.information(self, "Coller", "Aucune image à coller")
            return

        image = clipboard.image()
        if image.isNull():
            QMessageBox.information(self, "Coller", "Aucune image à coller")
            return

        image_path = self.pdf_service.cache_dir / f"clipboard_capture_{self.next_source_id}.png"
        if not image.save(str(image_path), "PNG"):
            QMessageBox.warning(self, "Coller", "Impossible de lire l'image du presse-papier.")
            return

        color = SOURCE_COLORS[(self.next_source_id - 1) % len(SOURCE_COLORS)]
        source_id = self.next_source_id
        self.next_source_id += 1
        try:
            page = self.pdf_service.capture_page(image_path, source_id, color)
        except Exception as exc:
            QMessageBox.warning(self, "Coller", f"Impossible d'ajouter la capture.\n{exc}")
            return

        self.pages.append(page)
        self.sources.append(page.source)
        self.board.set_pages(self.pages)
        last_row = len(self.pages) - 1
        self.board.list_widget.setCurrentRow(last_row)
        self.board.list_widget.scrollToItem(self.board.list_widget.item(last_row))
        self.statusBar().showMessage("Capture ajoutée", 2500)

    def move_page(self, source_indexes: list[int], target_index: int) -> None:
        valid_indexes = sorted({index for index in source_indexes if 0 <= index < len(self.pages)})
        if not valid_indexes:
            return
        moving_pages = [self.pages[index] for index in valid_indexes]
        for index in reversed(valid_indexes):
            self.pages.pop(index)
            if index < target_index:
                target_index -= 1
        target_index = max(0, min(target_index, len(self.pages)))
        for offset, page in enumerate(moving_pages):
            self.pages.insert(target_index + offset, page)
        self.board.set_pages(self.pages)

    def set_page_order(self, pages: list[PageItem]) -> None:
        self.pages = pages

    def delete_pages(self, page_indexes: list[int]) -> None:
        valid_indexes = sorted({index for index in page_indexes if 0 <= index < len(self.pages)}, reverse=True)
        if not valid_indexes:
            return
        for index in valid_indexes:
            self.pages.pop(index)
        self.board.clear_selection()
        self.board.set_pages(self.pages)

    def delete_all_pages(self) -> None:
        if not self.pages:
            return
        answer = QMessageBox.question(
            self,
            "Supprimer toutes les pages",
            "Supprimer toutes les pages du montage ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.pages.clear()
        self.board.clear_selection()
        self.board.set_pages(self.pages)

    def open_separator_dialog(self, insert_index: int) -> None:
        options = self.pdf_service.separators(self.separator_folder)
        if not options:
            QMessageBox.information(
                self,
                "Aucun separateur",
                "Ajoutez des fichiers PDF dans le dossier separateurs/ puis reessayez.",
            )
            return
        dialog = SeparatorDialog(options, self)
        if dialog.exec() and dialog.selected:
            color = "#64748b"
            source = SourceDocument(self.next_source_id, dialog.selected.path, color)
            self.next_source_id += 1
            try:
                separator_pages = self.pdf_service.separator_pages(source)
            except Exception as exc:
                QMessageBox.warning(self, "Separateur impossible", str(exc))
                return
            for offset, item in enumerate(separator_pages):
                self.pages.insert(insert_index + offset, item)
            self.board.set_pages(self.pages)

    def generate_pdf(self) -> None:
        if not self.pages:
            QMessageBox.information(self, "PDF manquant", "Importez au moins une page PDF.")
            return

        try:
            output_date = date(
                self.year_spin.value(),
                self.month_spin.value(),
                self.day_spin.value(),
            )
        except ValueError:
            QMessageBox.warning(self, "Date invalide", "Verifiez les champs JJ / MM / AAAA.")
            return

        name = self._normalize_name_part(self.name_edit.text(), uppercase=True)
        firstname = self._normalize_name_part(self.firstname_edit.text(), uppercase=False)
        if not name or not firstname:
            QMessageBox.information(self, "Nom incomplet", "Renseignez le nom et le prenom.")
            return

        suffix = "_P" if self.suffix_check.isChecked() else ""
        filename = f"{output_date:%Y-%m-%d}_{name}-{firstname}{suffix}.pdf"
        output_path = self.output_folder / filename
        try:
            self.pdf_service.merge(self.pages, output_path)
            save_last_date(output_date)
        except Exception as exc:
            QMessageBox.critical(self, "Generation impossible", str(exc))
            return

        self.last_output_path = output_path
        self._show_result(output_path)

    def reset_case(self) -> None:
        self.sources.clear()
        self.pages.clear()
        self.next_source_id = 1
        self.last_output_path = None
        self.name_edit.clear()
        self.firstname_edit.clear()
        self.suffix_check.setChecked(True)
        self.board.set_pages(self.pages)
        self.stack.setCurrentWidget(self.editor_page)

    def _normalize_name_part(self, text: str, uppercase: bool) -> str:
        normalized = unicodedata.normalize("NFKD", text)
        without_accents = "".join(
            char for char in normalized if not unicodedata.combining(char)
        )
        with_spaces = re.sub(r"[-'\u2019`\u00b4]", " ", without_accents)
        alphanumeric_spaces = re.sub(r"[^A-Za-z0-9 ]+", "", with_spaces)
        compact = re.sub(r"\s+", " ", alphanumeric_spaces).strip()
        if uppercase:
            return compact.upper()
        return compact[:1].upper() + compact[1:].lower() if compact else ""

    def _pdfs_from_event(self, event) -> list[Path]:
        return pdf_paths_from_mime(event.mimeData())

    def _apply_style(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow, QWidget {
                background: #111827;
                color: #f9fafb;
                font-family: "Segoe UI", Arial, sans-serif;
                font-size: 10pt;
            }
            QLabel {
                color: #f9fafb;
                background: transparent;
            }
            QLineEdit, QSpinBox {
                background: #f9fafb;
                color: #111827;
                border: 1px solid #64748b;
                border-radius: 5px;
                padding: 6px 8px;
                selection-background-color: #2563eb;
                selection-color: #ffffff;
            }
            QLineEdit:focus, QSpinBox:focus {
                border: 2px solid #60a5fa;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                subcontrol-origin: border;
                width: 22px;
                background: #dbeafe;
                border-left: 1px solid #94a3b8;
            }
            QSpinBox::up-button {
                subcontrol-position: top right;
                border-top-right-radius: 4px;
            }
            QSpinBox::down-button {
                subcontrol-position: bottom right;
                border-bottom-right-radius: 4px;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background: #bfdbfe;
            }
            QPushButton {
                background: #2563eb;
                color: #ffffff;
                border: none;
                border-radius: 5px;
                padding: 8px 12px;
                font-weight: 600;
            }
            QPushButton:hover { background: #1d4ed8; }
            QPushButton:pressed { background: #1e40af; }
            QToolButton {
                background: #334155;
                color: #ffffff;
                border: 1px solid #64748b;
                border-radius: 5px;
                min-width: 26px;
                min-height: 28px;
                font-size: 15px;
                font-weight: 700;
            }
            QToolButton:hover {
                background: #475569;
                border-color: #93c5fd;
            }
            QToolButton:pressed {
                background: #1d4ed8;
            }
            QCheckBox {
                color: #f9fafb;
                spacing: 8px;
                background: transparent;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                background: #f9fafb;
                border: 1px solid #94a3b8;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                background: #2563eb;
                border: 1px solid #93c5fd;
            }
            QScrollArea {
                border: 1px solid #374151;
                background: #0f172a;
            }
            QScrollArea > QWidget > QWidget {
                background: #0f172a;
            }
            QMenu {
                background: #1f2937;
                color: #f9fafb;
                border: 1px solid #4b5563;
            }
            QMenu::item:selected {
                background: #2563eb;
            }
            QMessageBox {
                background: #111827;
            }
            """
        )


def main() -> None:
    set_windows_app_id()
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(str(resource_path(APP_ICON_PATH))))
    window = MultiPrepWindow()
    window.show()
    sys.exit(app.exec())
