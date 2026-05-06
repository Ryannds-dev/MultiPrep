from __future__ import annotations

import shutil
from copy import copy
from pathlib import Path
from typing import Sequence

import fitz
from pypdf import PdfReader, PdfWriter

from multiprep.models.page_model import PageItem, SeparatorOption, SourceDocument
from multiprep.services.thumbnail_service import render_thumbnail
from multiprep.utils.paths import CACHE_DIR

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}


class PdfService:
    def __init__(self, cache_dir: Path | None = None) -> None:
        self.cache_dir = cache_dir or CACHE_DIR
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir, ignore_errors=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def cleanup(self) -> None:
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir, ignore_errors=True)

    def document_pages(self, source: SourceDocument) -> list[PageItem]:
        pages: list[PageItem] = []
        with fitz.open(source.path) as doc:
            for index, page in enumerate(doc):
                thumb = render_thumbnail(page, self.cache_dir / f"doc_{source.id}_page_{index}.png")
                pages.append(PageItem(source, index, thumb, f"p.{index + 1}"))
        return pages

    def separators(self, folder: Path) -> list[SeparatorOption]:
        folder.mkdir(exist_ok=True)
        options: list[SeparatorOption] = []
        for path in sorted(folder.glob("*.pdf")):
            try:
                with fitz.open(path) as doc:
                    preview = None
                    if len(doc):
                        preview = render_thumbnail(doc[0], self.cache_dir / f"sep_{abs(hash(path))}.png")
                    options.append(SeparatorOption(path.stem, path, len(doc), preview))
            except Exception:
                continue
        return options

    def separator_pages(self, source: SourceDocument) -> list[PageItem]:
        items: list[PageItem] = []
        with fitz.open(source.path) as doc:
            for index, page in enumerate(doc):
                thumb = render_thumbnail(page, self.cache_dir / f"separator_{source.id}_page_{index}.png")
                label = source.display_stem if len(doc) == 1 else f"{source.display_stem} {index + 1}"
                items.append(PageItem(source, index, thumb, label, is_separator=True))
        return items

    def capture_page(self, image_path: Path, source_id: int, color: str) -> PageItem:
        pdf_path = self.cache_dir / f"capture_{source_id}.pdf"
        return self._image_pdf_page(image_path, pdf_path, source_id, color, "Capture", "capture")

    def image_page(self, image_path: Path, source_id: int, color: str) -> PageItem:
        pdf_path = self.cache_dir / f"image_{source_id}.pdf"
        return self._image_pdf_page(image_path, pdf_path, source_id, color, image_path.name, "image")

    def _image_pdf_page(
        self,
        image_path: Path,
        pdf_path: Path,
        source_id: int,
        color: str,
        label: str,
        page_type: str,
    ) -> PageItem:
        with fitz.open() as doc:
            pixmap = fitz.Pixmap(str(image_path))
            page = doc.new_page(width=pixmap.width, height=pixmap.height)
            page.insert_image(page.rect, filename=str(image_path))
            doc.save(pdf_path)

        display_name = SourceDocument(source_id, image_path, color).display_name if page_type == "image" else None
        source = SourceDocument(source_id, pdf_path, color, display_name)
        with fitz.open(pdf_path) as doc:
            thumb = render_thumbnail(doc[0], self.cache_dir / f"{page_type}_{source_id}_thumb.png")
        return PageItem(source, 0, thumb, label, page_type=page_type)

    def merge(self, pages: Sequence[PageItem], output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        writer = PdfWriter()
        readers: dict[Path, PdfReader] = {}

        for item in pages:
            reader = readers.get(item.source.path)
            if reader is None:
                reader = PdfReader(str(item.source.path))
                readers[item.source.path] = reader
            page = copy(reader.pages[item.page_index])
            if item.rotation % 360:
                page.rotate(item.rotation % 360)
            writer.add_page(page)

        with output_path.open("wb") as handle:
            writer.write(handle)
