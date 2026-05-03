from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QApplication

from multiprep.models.page_model import PageItem
from multiprep.services.pdf_service import PdfService


class ClipboardService:
    def __init__(self, pdf_service: PdfService) -> None:
        self.pdf_service = pdf_service

    def has_image(self) -> bool:
        return QApplication.clipboard().mimeData().hasImage()

    def paste_image_as_page(self, source_id: int, color: str) -> PageItem | None:
        image = QApplication.clipboard().image()
        if image.isNull():
            return None

        image_path = self.pdf_service.cache_dir / f"clipboard_capture_{source_id}.png"
        if not image.save(str(image_path), "PNG"):
            return None
        return self.pdf_service.capture_page(image_path, source_id, color)
