from __future__ import annotations

import base64
import struct
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PySide6.QtCore import QByteArray, QMimeData, QUrl
from PySide6.QtGui import QColor, QImage

from multiprep.services import drop_service


class DropServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.mail_dir_patch = patch.object(drop_service, "MAIL_DROP_DIR", Path(self.temp_dir.name))
        self.mail_dir_patch.start()

    def tearDown(self) -> None:
        self.mail_dir_patch.stop()
        self.temp_dir.cleanup()

    def test_local_supported_file(self) -> None:
        path = Path(self.temp_dir.name) / "document.pdf"
        path.write_bytes(b"%PDF-1.4")
        mime = QMimeData()
        mime.setUrls([QUrl.fromLocalFile(str(path))])

        self.assertTrue(drop_service.has_supported_file_mime(mime))
        self.assertEqual(drop_service.file_paths_from_mime(mime), [path])

    def test_qt_image_drop_is_saved_as_png(self) -> None:
        mime = QMimeData()
        image = QImage(3, 2, QImage.Format.Format_RGB32)
        image.fill(QColor("red"))
        mime.setImageData(image)

        self.assertTrue(drop_service.has_supported_file_mime(mime))
        paths = drop_service.file_paths_from_mime(mime)
        self.assertEqual(len(paths), 1)
        self.assertFalse(QImage(str(paths[0])).isNull())

    def test_html_data_image_drop_is_saved(self) -> None:
        image = QImage(2, 2, QImage.Format.Format_RGB32)
        image.fill(QColor("blue"))
        source = Path(self.temp_dir.name) / "source.png"
        image.save(str(source), "PNG")
        encoded = base64.b64encode(source.read_bytes())
        mime = QMimeData()
        mime.setData("text/html", QByteArray(b'<img src="data:image/png;base64,' + encoded + b'">'))

        self.assertTrue(drop_service.has_supported_file_mime(mime))
        paths = drop_service.file_paths_from_mime(mime)
        self.assertEqual(len(paths), 1)
        self.assertFalse(QImage(str(paths[0])).isNull())

    def test_chromium_download_url_uses_virtual_file_contents(self) -> None:
        mime = QMimeData()
        mime.setData(
            'application/x-qt-windows-mime;value="DownloadURL"',
            QByteArray(b"application/pdf:piece%20jointe.pdf:https://mail.google.test/download"),
        )
        mime.setData(
            'application/x-qt-windows-mime;value="FileContents"',
            QByteArray(b"%PDF-1.7 test"),
        )

        self.assertTrue(drop_service.has_supported_file_mime(mime))
        paths = drop_service.file_paths_from_mime(mime)
        self.assertEqual([path.name for path in paths], ["piece jointe.pdf"])
        self.assertEqual(paths[0].read_bytes(), b"%PDF-1.7 test")

    def test_outlook_unicode_descriptor_still_works(self) -> None:
        filename = "scan.png"
        descriptor = bytearray(592)
        encoded_name = filename.encode("utf-16le") + b"\x00\x00"
        descriptor[72:72 + len(encoded_name)] = encoded_name
        mime = QMimeData()
        mime.setData(
            'application/x-qt-windows-mime;value="FileGroupDescriptorW"',
            QByteArray(struct.pack("<I", 1) + descriptor),
        )
        mime.setData(
            'application/x-qt-windows-mime;value="FileContents";index=0',
            QByteArray(b"fake image bytes"),
        )

        paths = drop_service.file_paths_from_mime(mime)
        self.assertEqual([path.name for path in paths], [filename])
        self.assertEqual(paths[0].read_bytes(), b"fake image bytes")


if __name__ == "__main__":
    unittest.main()
