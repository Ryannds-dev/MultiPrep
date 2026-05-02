from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class SourceDocument:
    id: int
    path: Path
    color: str


@dataclass
class PageItem:
    source: SourceDocument
    page_index: int
    thumbnail_path: Path
    label: str
    is_separator: bool = False

    @property
    def display_name(self) -> str:
        if self.is_separator:
            return self.source.path.stem
        return f"{self.source.path.name} - p.{self.page_index + 1}"


@dataclass(frozen=True)
class SeparatorOption:
    name: str
    path: Path
    page_count: int
    preview_path: Optional[Path] = None
