from __future__ import annotations

import shutil
from pathlib import Path, PureWindowsPath

from PySide6.QtCore import QMimeData

from multiprep.utils.paths import MAIL_DROP_DIR

PDF_EXTENSIONS = {".pdf"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
SUPPORTED_EXTENSIONS = PDF_EXTENSIONS | IMAGE_EXTENSIONS


def has_supported_file_mime(mime_data: QMimeData) -> bool:
    if _local_supported_paths(mime_data):
        return True
    return any(_is_supported_path(name) for name in _windows_attachment_names(mime_data))


def file_paths_from_mime(mime_data: QMimeData) -> list[Path]:
    local_paths = _local_supported_paths(mime_data)
    if local_paths:
        return local_paths
    return _extract_windows_supported_attachments(mime_data)


def cleanup_mail_drop_dir() -> None:
    shutil.rmtree(MAIL_DROP_DIR, ignore_errors=True)


def _local_supported_paths(mime_data: QMimeData) -> list[Path]:
    if not mime_data.hasUrls():
        return []
    return [
        Path(url.toLocalFile())
        for url in mime_data.urls()
        if url.isLocalFile() and _is_supported_path(url.toLocalFile())
    ]


def _extract_windows_supported_attachments(mime_data: QMimeData) -> list[Path]:
    names = _windows_attachment_names(mime_data)
    if not names:
        return []

    MAIL_DROP_DIR.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for index, name in enumerate(names):
        if not _is_supported_path(name):
            continue
        data = _windows_file_contents(mime_data, index)
        if not data:
            continue
        path = _available_attachment_path(_safe_attachment_name(name))
        path.write_bytes(data)
        paths.append(path)
    return paths


def _safe_attachment_name(name: str) -> str:
    filename = PureWindowsPath(name).name.replace("/", "_").replace("\\", "_").strip()
    return filename or "piece_jointe.pdf"


def _available_attachment_path(filename: str) -> Path:
    path = MAIL_DROP_DIR / filename
    if not path.exists():
        return path

    stem = path.stem
    suffix = path.suffix
    counter = 1
    while True:
        candidate = MAIL_DROP_DIR / f"{stem} ({counter}){suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def _is_supported_path(path: str) -> bool:
    return Path(path).suffix.lower() in SUPPORTED_EXTENSIONS


def _windows_attachment_names(mime_data: QMimeData) -> list[str]:
    fmt = _find_windows_mime_format(mime_data, "FileGroupDescriptorW")
    if fmt:
        return _parse_file_group_descriptor(bytes(mime_data.data(fmt)), 592, 72, 520, "utf-16le")
    fmt = _find_windows_mime_format(mime_data, "FileGroupDescriptor")
    if fmt:
        return _parse_file_group_descriptor(bytes(mime_data.data(fmt)), 332, 72, 260, "mbcs")
    return []


def _find_windows_mime_format(mime_data: QMimeData, value: str, index: int | None = None) -> str | None:
    for fmt in mime_data.formats():
        if f'value="{value}"' not in fmt:
            continue
        if index is not None and f"index={index}" not in fmt:
            continue
        return fmt
    return None


def _windows_file_contents(mime_data: QMimeData, index: int) -> bytes:
    fmt = _find_windows_mime_format(mime_data, "FileContents", index)
    if fmt is None and index == 0:
        fmt = _find_windows_mime_format(mime_data, "FileContents")
    return bytes(mime_data.data(fmt)) if fmt else b""


def _parse_file_group_descriptor(
    data: bytes,
    descriptor_size: int,
    name_offset: int,
    name_size: int,
    encoding: str,
) -> list[str]:
    if len(data) < 4:
        return []
    count = int.from_bytes(data[:4], "little", signed=False)
    names: list[str] = []
    for index in range(count):
        start = 4 + index * descriptor_size + name_offset
        raw_name = data[start:start + name_size]
        if encoding == "utf-16le":
            terminator = raw_name.find(b"\x00\x00")
            if terminator != -1:
                terminator += terminator % 2
                raw_name = raw_name[:terminator]
        else:
            raw_name = raw_name.split(b"\x00", 1)[0]
        name = raw_name.decode(encoding, errors="ignore").strip("\x00").strip()
        if name:
            names.append(name)
    return names
