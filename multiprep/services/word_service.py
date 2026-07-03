from __future__ import annotations

import os
import subprocess
from pathlib import Path


WORD_EXTENSIONS = {".doc", ".docx"}
WORD_TO_PDF_SCRIPT = r"""
$ErrorActionPreference = "Stop"
$word = $null
$document = $null
try {
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $document = $word.Documents.Open($env:MULTIPREP_WORD_INPUT, $false, $true)
    $document.ExportAsFixedFormat($env:MULTIPREP_WORD_OUTPUT, 17)
}
finally {
    if ($null -ne $document) {
        $document.Close(0)
    }
    if ($null -ne $word) {
        $word.Quit()
    }
    [System.GC]::Collect()
    [System.GC]::WaitForPendingFinalizers()
}
"""


class WordConversionError(RuntimeError):
    pass


def convert_word_to_pdf(source_path: Path, output_path: Path) -> Path:
    if source_path.suffix.lower() not in WORD_EXTENSIONS:
        raise WordConversionError(f"Format Word non pris en charge : {source_path.suffix}")
    if not source_path.is_file():
        raise WordConversionError(f"Fichier Word introuvable : {source_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.unlink(missing_ok=True)
    environment = os.environ.copy()
    environment["MULTIPREP_WORD_INPUT"] = str(source_path.resolve())
    environment["MULTIPREP_WORD_OUTPUT"] = str(output_path.resolve())

    creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    try:
        result = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                WORD_TO_PDF_SCRIPT,
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=environment,
            timeout=120,
            creationflags=creation_flags,
            check=False,
        )
    except FileNotFoundError as exc:
        raise WordConversionError("PowerShell est indisponible sur ce poste.") from exc
    except subprocess.TimeoutExpired as exc:
        raise WordConversionError("La conversion Word a dépassé le délai de deux minutes.") from exc

    if result.returncode != 0 or not output_path.is_file():
        details = (result.stderr or result.stdout).strip()
        message = "Microsoft Word n’a pas pu convertir ce document en PDF."
        if details:
            message += f"\n{details}"
        raise WordConversionError(message)
    return output_path
