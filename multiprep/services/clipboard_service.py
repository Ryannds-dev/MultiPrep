from __future__ import annotations

from PySide6.QtWidgets import QApplication

from multiprep.models.page_model import PageItem
from multiprep.services.drop_service import file_paths_from_mime
from multiprep.services.pdf_service import PdfService


class ClipboardService:
    def __init__(self, pdf_service: PdfService) -> None:
        self.pdf_service = pdf_service

    def paste_image_as_page(self, source_id: int, color: str) -> PageItem | None:
        paths = file_paths_from_mime(QApplication.clipboard().mimeData())
        if not paths:
            return None
        image_path = paths[0]
        if image_path.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
            return None
        return self.pdf_service.capture_page(image_path, source_id, color)
