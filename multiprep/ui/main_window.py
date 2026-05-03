from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QIcon, QKeySequence
from PySide6.QtWidgets import QCheckBox, QLineEdit, QMainWindow, QStackedWidget

from multiprep.models.page_model import PageItem, SourceDocument
from multiprep.services.clipboard_service import ClipboardService
from multiprep.services.drop_service import cleanup_mail_drop_dir, has_pdf_mime, pdf_paths_from_mime
from multiprep.services.pdf_service import PdfService
from multiprep.services.settings_service import load_settings
from multiprep.ui.date_widgets import DateSpin
from multiprep.ui.editor_view import EditorView
from multiprep.ui.main_window_actions import MainWindowActionsMixin
from multiprep.ui.page_board import PageBoard
from multiprep.ui.result_view import ResultView
from multiprep.ui.styles import APP_STYLE
from multiprep.utils.paths import APP_ICON_PATH, EXPORTS_DIR, SEPARATORS_DIR, resource_path


class MultiPrepWindow(MainWindowActionsMixin, QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("MultiPrep")
        self.setWindowIcon(QIcon(str(resource_path(APP_ICON_PATH))))
        self.resize(1180, 760)
        self.setAcceptDrops(True)

        self.pdf_service = PdfService()
        self.clipboard_service = ClipboardService(self.pdf_service)
        self.pages: list[PageItem] = []
        self.sources: list[SourceDocument] = []
        self.next_source_id = 1
        self.last_output_path: Path | None = None
        self.separator_folder = SEPARATORS_DIR
        self.output_folder = EXPORTS_DIR

        self._init_fields()
        self._build_pages()
        self._apply_style()

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
        pdfs = pdf_paths_from_mime(event.mimeData())
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

    def _init_fields(self) -> None:
        settings = load_settings()
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Nom")
        self.firstname_edit = QLineEdit()
        self.firstname_edit.setPlaceholderText("Prénom")
        self.day_spin = self._spin(1, 31, settings.last_date.day)
        self.month_spin = self._spin(1, 12, settings.last_date.month)
        self.year_spin = self._spin(1900, 2200, settings.last_date.year)
        self.suffix_check = QCheckBox("P")
        self.suffix_check.setChecked(True)

    def _build_pages(self) -> None:
        self.stack = QStackedWidget()
        self.board = self._create_board()
        self.editor_page = EditorView(
            self.name_edit,
            self.firstname_edit,
            self.day_spin,
            self.month_spin,
            self.year_spin,
            self.suffix_check,
            self.board,
            self.choose_pdfs,
            self.generate_pdf,
        )
        self.result_page = ResultView()
        self.result_page.cancel_requested.connect(lambda: self.stack.setCurrentWidget(self.editor_page))
        self.result_page.new_case_requested.connect(self.reset_case)
        self.stack.addWidget(self.editor_page)
        self.stack.addWidget(self.result_page)
        self.setCentralWidget(self.stack)
        self.board.set_pages(self.pages)

    def _create_board(self) -> PageBoard:
        board = PageBoard()
        board.pdfs_dropped.connect(self.add_pdfs)
        board.order_changed.connect(self.set_page_order)
        board.separator_requested.connect(self.open_separator_dialog)
        board.delete_pages_requested.connect(self.delete_pages)
        board.delete_all_requested.connect(self.delete_all_pages)
        board.paste_requested.connect(self.handle_paste)
        return board

    def _spin(self, minimum: int, maximum: int, value: int) -> DateSpin:
        digits = 2 if maximum <= 31 else 4
        return DateSpin(minimum, maximum, value, 66 if maximum > 99 else 46, digits)

    def _apply_style(self) -> None:
        self.setStyleSheet(APP_STYLE)
