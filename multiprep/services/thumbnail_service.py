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
