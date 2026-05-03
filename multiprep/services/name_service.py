from __future__ import annotations

import re
import unicodedata
from datetime import date


def normalize_name_part(text: str, uppercase: bool) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    without_accents = "".join(char for char in normalized if not unicodedata.combining(char))
    with_spaces = re.sub(r"[-'\u2019`\u00b4]", " ", without_accents)
    alphanumeric_spaces = re.sub(r"[^A-Za-z0-9 ]+", "", with_spaces)
    compact = re.sub(r"\s+", " ", alphanumeric_spaces).strip()
    if uppercase:
        return compact.upper()
    return compact[:1].upper() + compact[1:].lower() if compact else ""


def build_output_filename(output_date: date, name: str, firstname: str, with_suffix: bool) -> str:
    suffix = "_P" if with_suffix else ""
    return f"{output_date:%Y-%m-%d}_{name}-{firstname}{suffix}.pdf"
