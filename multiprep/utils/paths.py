from __future__ import annotations

import sys
from pathlib import Path


APP_ICON_PATH = Path("assets") / "multiprep-logo.ico"
SEPARATORS_DIR = Path("separateurs")
EXPORTS_DIR = Path("exports")
SETTINGS_FILE = Path("settings.json")
TEMP_DIR = Path("temp")
CACHE_DIR = TEMP_DIR / "cache"
MAIL_DROP_DIR = TEMP_DIR / "mail_attachments"


def resource_path(relative_path: Path) -> Path:
    base_path = Path(getattr(sys, "_MEIPASS", Path.cwd()))
    return base_path / relative_path
