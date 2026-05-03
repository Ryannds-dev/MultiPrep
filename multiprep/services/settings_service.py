from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date

from multiprep.utils.paths import SETTINGS_FILE


@dataclass
class AppSettings:
    last_date: date


def load_settings() -> AppSettings:
    today = date.today()
    if not SETTINGS_FILE.exists():
        return AppSettings(last_date=today)

    try:
        raw = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        year, month, day = [int(part) for part in raw.get("last_date", "").split("-")]
        return AppSettings(last_date=date(year, month, day))
    except Exception:
        return AppSettings(last_date=today)


def save_last_date(value: date) -> None:
    SETTINGS_FILE.write_text(
        json.dumps({"last_date": value.isoformat()}, indent=2),
        encoding="utf-8",
    )
