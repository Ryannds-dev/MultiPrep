from __future__ import annotations

from pathlib import Path

import fitz


THUMBNAIL_WIDTH = 180


def render_thumbnail(page: fitz.Page, output_path: Path) -> Path:
    zoom = THUMBNAIL_WIDTH / page.rect.width
    matrix = fitz.Matrix(zoom, zoom)
    pixmap = page.get_pixmap(matrix=matrix, alpha=False)
    pixmap.save(output_path)
    return output_path


def ensure_page_thumbnails(page_items: list) -> None:
    """Render missing PDF thumbnails while opening each source only once."""
    pending_by_source: dict[Path, list] = {}
    for page in page_items:
        source_path = Path(page.source.path)
        output_path = Path(page.thumbnail_path)
        if source_path.suffix.lower() != ".pdf" or output_path.is_file():
            continue
        pending_by_source.setdefault(source_path, []).append(page)

    for source_path, pages in pending_by_source.items():
        with fitz.open(source_path) as document:
            for page in pages:
                output_path = Path(page.thumbnail_path)
                if not output_path.is_file():
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    render_thumbnail(document[page.page_index], output_path)
