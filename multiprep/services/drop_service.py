from __future__ import annotations

import base64
import binascii
import html as html_module
import re
import shutil
import urllib.request
from pathlib import Path, PureWindowsPath
from urllib.parse import unquote

from PySide6.QtCore import QMimeData
from PySide6.QtGui import QImage, QPixmap

from multiprep.utils.paths import MAIL_DROP_DIR

PDF_EXTENSIONS = {".pdf"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
WORD_EXTENSIONS = {".doc", ".docx"}
SUPPORTED_EXTENSIONS = PDF_EXTENSIONS | IMAGE_EXTENSIONS | WORD_EXTENSIONS
RAW_IMAGE_FORMATS = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
}
DATA_IMAGE_PATTERN = re.compile(
    rb"""data:(image/(?:png|jpe?g))(?:;[^,]*)?;base64,([a-zA-Z0-9+/=\s]+)""",
    re.IGNORECASE,
)
HTML_IMAGE_URL_PATTERN = re.compile(
    rb"""<img[^>]+src\s*=\s*["'](https?://[^"']+)""",
    re.IGNORECASE,
)


def has_supported_file_mime(mime_data: QMimeData) -> bool:
    if _local_supported_paths(mime_data):
        return True
    names = _virtual_attachment_names(mime_data)
    if any(_is_supported_path(name) for name in names):
        return True
    if _has_embedded_image(mime_data):
        return True
    return False


def file_paths_from_mime(mime_data: QMimeData) -> list[Path]:
    local_paths = _local_supported_paths(mime_data)
    if local_paths:
        return local_paths
    virtual_paths = _extract_virtual_supported_attachments(mime_data)
    if virtual_paths:
        return virtual_paths
    image_path = _extract_embedded_image(mime_data)
    return [image_path] if image_path else []


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


def _extract_virtual_supported_attachments(mime_data: QMimeData) -> list[Path]:
    names = _virtual_attachment_names(mime_data)
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


def _extract_embedded_image(mime_data: QMimeData) -> Path | None:
    image = _qt_image(mime_data)
    if image is None:
        image = _raw_mime_image(mime_data)
    if image is None:
        image = _html_data_image(mime_data)
    if image is None:
        image = _html_remote_image(mime_data)
    if image is None or image.isNull():
        return None

    MAIL_DROP_DIR.mkdir(parents=True, exist_ok=True)
    path = _available_attachment_path("image_glissee.png")
    return path if image.save(str(path), "PNG") else None


def _has_embedded_image(mime_data: QMimeData) -> bool:
    if mime_data.hasImage():
        return True
    formats = {fmt.lower() for fmt in mime_data.formats()}
    if any(fmt in formats for fmt in RAW_IMAGE_FORMATS):
        return True
    html = _mime_bytes(mime_data, "text/html")
    return bool(html and (DATA_IMAGE_PATTERN.search(html) or HTML_IMAGE_URL_PATTERN.search(html)))


def _qt_image(mime_data: QMimeData) -> QImage | None:
    if not mime_data.hasImage():
        return None
    value = mime_data.imageData()
    if isinstance(value, QImage):
        return value
    if isinstance(value, QPixmap):
        return value.toImage()
    return None


def _raw_mime_image(mime_data: QMimeData) -> QImage | None:
    for mime_type in RAW_IMAGE_FORMATS:
        data = _mime_bytes(mime_data, mime_type)
        if data:
            image = QImage.fromData(data)
            if not image.isNull():
                return image
    return None


def _html_data_image(mime_data: QMimeData) -> QImage | None:
    html = _mime_bytes(mime_data, "text/html")
    match = DATA_IMAGE_PATTERN.search(html)
    if not match:
        return None
    try:
        data = base64.b64decode(match.group(2), validate=False)
    except (ValueError, binascii.Error):
        return None
    image = QImage.fromData(data)
    return image if not image.isNull() else None


def _html_remote_image(mime_data: QMimeData) -> QImage | None:
    html = _mime_bytes(mime_data, "text/html")
    match = HTML_IMAGE_URL_PATTERN.search(html)
    if not match:
        return None
    url = html_module.unescape(match.group(1).decode("utf-8", errors="replace"))
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(request, timeout=8) as response:
            data = response.read(25 * 1024 * 1024)
    except (OSError, ValueError):
        return None
    image = QImage.fromData(data)
    return image if not image.isNull() else None


def _mime_bytes(mime_data: QMimeData, wanted_format: str) -> bytes:
    wanted = wanted_format.lower()
    for fmt in mime_data.formats():
        if fmt.lower() == wanted:
            return bytes(mime_data.data(fmt))
    return b""


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


def _browser_download_names(mime_data: QMimeData) -> list[str]:
    data = _mime_bytes(mime_data, "DownloadURL")
    if not data:
        fmt = _find_windows_mime_format(mime_data, "DownloadURL")
        data = bytes(mime_data.data(fmt)) if fmt else b""
    if not data:
        return []
    # Some browsers expose "mime-type:file-name:url". The URL may itself contain
    # colons, hence the deliberately limited split.
    parts = data.decode("utf-8", errors="replace").split(":", 2)
    if len(parts) != 3:
        return []
    filename = unquote(parts[1]).strip().strip('"')
    return [filename] if filename else []


def _virtual_attachment_names(mime_data: QMimeData) -> list[str]:
    return _windows_attachment_names(mime_data) or _browser_download_names(mime_data)


def _find_windows_mime_format(mime_data: QMimeData, value: str, index: int | None = None) -> str | None:
    value_marker = f'value="{value}"'.lower()
    for fmt in mime_data.formats():
        normalized = fmt.lower().replace(" ", "")
        if value_marker not in normalized:
            continue
        if index is not None and f"index={index}" not in normalized:
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
