from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from multiprep.services.word_service import WordConversionError, convert_word_to_pdf


class WordServiceTests(unittest.TestCase):
    def test_conversion_passes_paths_without_shell_interpolation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "document avec espaces.docx"
            output = root / "document.pdf"
            source.write_bytes(b"docx")

            def fake_run(*_args, **kwargs):
                self.assertEqual(kwargs["env"]["MULTIPREP_WORD_INPUT"], str(source.resolve()))
                self.assertEqual(kwargs["env"]["MULTIPREP_WORD_OUTPUT"], str(output.resolve()))
                output.write_bytes(b"%PDF-1.7")
                return subprocess.CompletedProcess([], 0, "", "")

            with patch("multiprep.services.word_service.subprocess.run", side_effect=fake_run):
                self.assertEqual(convert_word_to_pdf(source, output), output)

    def test_conversion_reports_word_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "document.doc"
            source.write_bytes(b"doc")
            output = Path(directory) / "document.pdf"
            failed = subprocess.CompletedProcess([], 1, "", "Word indisponible")

            with patch("multiprep.services.word_service.subprocess.run", return_value=failed):
                with self.assertRaisesRegex(WordConversionError, "Word indisponible"):
                    convert_word_to_pdf(source, output)


if __name__ == "__main__":
    unittest.main()
