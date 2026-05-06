from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class SourceDocument:
    id: int
    path: Path
    color: str
    display_name_override: str | None = None

    @property
    def display_name(self) -> str:
        if self.display_name_override:
            return self.display_name_override
        return _display_filename(self.path.name)

    @property
    def display_stem(self) -> str:
        return Path(self.display_name).stem


@dataclass
class PageItem:
    source: SourceDocument
    page_index: int
    thumbnail_path: Path
    label: str
    is_separator: bool = False
    page_type: str = "page"

    @property
    def display_name(self) -> str:
        if self.page_type == "capture":
            return self.label
        if self.page_type == "image":
            return self.source.display_name
        if self.is_separator:
            return self.source.display_stem
        return f"{self.source.display_name} - p.{self.page_index + 1}"


@dataclass(frozen=True)
class SeparatorOption:
    name: str
    path: Path
    page_count: int
    preview_path: Optional[Path] = None


def _display_filename(filename: str) -> str:
    uuid_prefix_length = 32
    if len(filename) > uuid_prefix_length + 1 and filename[uuid_prefix_length] == "_":
        prefix = filename[:uuid_prefix_length]
        if all(char in "0123456789abcdefABCDEF" for char in prefix):
            return filename[uuid_prefix_length + 1:]
    return filename
