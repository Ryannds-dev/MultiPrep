from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Iterable, Sequence

import fitz
from pypdf import PdfReader, PdfWriter

from .models import PageItem, SeparatorOption, SourceDocument


THUMBNAIL_WIDTH = 180


class PdfService:
    def __init__(self, cache_dir: Path | None = None) -> None:
        self.cache_dir = cache_dir or Path(tempfile.mkdtemp(prefix="multiprep_"))
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def cleanup(self) -> None:
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir, ignore_errors=True)

    def document_pages(self, source: SourceDocument) -> list[PageItem]:
        pages: list[PageItem] = []
        with fitz.open(source.path) as doc:
            for index, page in enumerate(doc):
                thumb = self._render_thumbnail(page, f"doc_{source.id}_page_{index}.png")
                pages.append(
                    PageItem(
                        source=source,
                        page_index=index,
                        thumbnail_path=thumb,
                        label=f"p.{index + 1}",
                    )
                )
        return pages

    def separators(self, folder: Path) -> list[SeparatorOption]:
        folder.mkdir(exist_ok=True)
        options: list[SeparatorOption] = []
        for path in sorted(folder.glob("*.pdf")):
            try:
                with fitz.open(path) as doc:
                    preview = None
                    if len(doc):
                        preview = self._render_thumbnail(doc[0], f"sep_{abs(hash(path))}.png")
                    options.append(
                        SeparatorOption(
                            name=path.stem,
                            path=path,
                            page_count=len(doc),
                            preview_path=preview,
                        )
                    )
            except Exception:
                continue
        return options

    def separator_pages(self, source: SourceDocument) -> list[PageItem]:
        items: list[PageItem] = []
        with fitz.open(source.path) as doc:
            for index, page in enumerate(doc):
                thumb = self._render_thumbnail(
                    page,
                    f"separator_{source.id}_page_{index}.png",
                )
                items.append(
                    PageItem(
                        source=source,
                        page_index=index,
                        thumbnail_path=thumb,
                        label=source.path.stem if len(doc) == 1 else f"{source.path.stem} {index + 1}",
                        is_separator=True,
                    )
                )
        return items

    def capture_page(self, image_path: Path, source_id: int, color: str) -> PageItem:
        pdf_path = self.cache_dir / f"capture_{source_id}.pdf"
        with fitz.open() as doc:
            pixmap = fitz.Pixmap(str(image_path))
            width = pixmap.width
            height = pixmap.height
            page = doc.new_page(width=width, height=height)
            page.insert_image(page.rect, filename=str(image_path))
            doc.save(pdf_path)

        source = SourceDocument(source_id, pdf_path, color)
        with fitz.open(pdf_path) as doc:
            thumb = self._render_thumbnail(doc[0], f"capture_{source_id}_thumb.png")
        return PageItem(
            source=source,
            page_index=0,
            thumbnail_path=thumb,
            label="Capture",
            page_type="capture",
        )

    def merge(self, pages: Sequence[PageItem], output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        writer = PdfWriter()
        readers: dict[Path, PdfReader] = {}

        for item in pages:
            reader = readers.get(item.source.path)
            if reader is None:
                reader = PdfReader(str(item.source.path))
                readers[item.source.path] = reader
            writer.add_page(reader.pages[item.page_index])

        with output_path.open("wb") as handle:
            writer.write(handle)

    def _render_thumbnail(self, page: fitz.Page, filename: str) -> Path:
        zoom = THUMBNAIL_WIDTH / page.rect.width
        matrix = fitz.Matrix(zoom, zoom)
        pixmap = page.get_pixmap(matrix=matrix, alpha=False)
        path = self.cache_dir / filename
        pixmap.save(path)
        return path
