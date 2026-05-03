from __future__ import annotations

from datetime import date
from pathlib import Path

from PySide6.QtWidgets import QFileDialog, QMessageBox

from multiprep.models.page_model import PageItem, SourceDocument
from multiprep.services.name_service import build_output_filename, normalize_name_part
from multiprep.services.settings_service import save_last_date
from multiprep.ui.dialogs import SeparatorDialog
from multiprep.utils.colors import SOURCE_COLORS


class MainWindowActionsMixin:
    def choose_pdfs(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(self, "Importer des PDF", str(Path.home()), "PDF (*.pdf)")
        self.add_pdfs([Path(path) for path in paths])

    def add_pdfs(self, paths: list[Path]) -> None:
        for path in paths:
            if not path.exists() or path.suffix.lower() != ".pdf":
                continue
            source = self._new_source(path)
            try:
                self.pages.extend(self.pdf_service.document_pages(source))
                self.sources.append(source)
            except Exception as exc:
                QMessageBox.warning(self, "Import impossible", f"{path.name}\n{exc}")
        self.board.set_pages(self.pages)

    def handle_paste(self) -> None:
        if not self.clipboard_service.has_image():
            QMessageBox.information(self, "Coller", "Aucune image a coller")
            return
        color = SOURCE_COLORS[(self.next_source_id - 1) % len(SOURCE_COLORS)]
        source_id = self.next_source_id
        self.next_source_id += 1
        page = self.clipboard_service.paste_image_as_page(source_id, color)
        if page is None:
            QMessageBox.warning(self, "Coller", "Impossible de lire l'image du presse-papier.")
            return
        self.pages.append(page)
        self.sources.append(page.source)
        self.board.set_pages(self.pages)
        self.board.list_widget.setCurrentRow(len(self.pages) - 1)
        self.statusBar().showMessage("Capture ajoutee", 2500)

    def set_page_order(self, pages: list[PageItem]) -> None:
        self.pages = pages

    def delete_pages(self, page_indexes: list[int]) -> None:
        valid_indexes = {i for i in page_indexes if 0 <= i < len(self.pages)}
        for index in sorted(valid_indexes, reverse=True):
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
        if answer == QMessageBox.StandardButton.Yes:
            self.pages.clear()
            self.board.clear_selection()
            self.board.set_pages(self.pages)

    def open_separator_dialog(self, insert_index: int) -> None:
        options = self.pdf_service.separators(self.separator_folder)
        if not options:
            QMessageBox.information(self, "Aucun separateur", "Ajoutez des PDF dans separateurs/ puis reessayez.")
            return
        dialog = SeparatorDialog(options, self)
        if dialog.exec() and dialog.selected:
            self._insert_separator_pages(dialog.selected.path, insert_index)

    def generate_pdf(self) -> None:
        if not self.pages:
            QMessageBox.information(self, "PDF manquant", "Importez au moins une page PDF.")
            return
        output_date = self._selected_date()
        if output_date is None:
            return
        name = normalize_name_part(self.name_edit.text(), uppercase=True)
        firstname = normalize_name_part(self.firstname_edit.text(), uppercase=False)
        if not name or not firstname:
            QMessageBox.information(self, "Nom incomplet", "Renseignez le nom et le prenom.")
            return
        filename = build_output_filename(output_date, name, firstname, self.suffix_check.isChecked())
        output_path = self.output_folder / filename
        try:
            self.pdf_service.merge(self.pages, output_path)
            save_last_date(output_date)
        except Exception as exc:
            QMessageBox.critical(self, "Génération impossible", str(exc))
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

    def _insert_separator_pages(self, path: Path, insert_index: int) -> None:
        source = self._new_source(path, color="#64748b")
        try:
            pages = self.pdf_service.separator_pages(source)
        except Exception as exc:
            QMessageBox.warning(self, "Separateur impossible", str(exc))
            return
        for offset, item in enumerate(pages):
            self.pages.insert(insert_index + offset, item)
        self.board.set_pages(self.pages)

    def _show_result(self, output_path: Path) -> None:
        self.result_page.show_output(output_path)
        self.stack.setCurrentWidget(self.result_page)

    def _selected_date(self) -> date | None:
        try:
            return date(self.year_spin.value(), self.month_spin.value(), self.day_spin.value())
        except ValueError:
            QMessageBox.warning(self, "Date invalide", "Verifiez les champs JJ / MM / AAAA.")
            return None

    def _new_source(self, path: Path, color: str | None = None) -> SourceDocument:
        source_color = color or SOURCE_COLORS[(self.next_source_id - 1) % len(SOURCE_COLORS)]
        source = SourceDocument(self.next_source_id, path, source_color)
        self.next_source_id += 1
        return source
