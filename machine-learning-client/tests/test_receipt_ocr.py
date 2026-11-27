"""Image-to-fields tests for the receipt OCR client."""

from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from receipts.ocr import ReceiptOCRError, extract_text, main


SAMPLE = Path(__file__).parent / "fixtures" / "corner-deli.png"


class ReceiptOCRTests(unittest.TestCase):
    """Verify real recognition and common failures."""

    def test_image_to_json(self):
        """The CLI reads pixels, keeps the recognized text, and parses the sale."""
        with patch.object(sys, "argv", ["ocr", str(SAMPLE)]):
            with redirect_stdout(io.StringIO()) as output:
                self.assertEqual(main(), 0)
        result = json.loads(output.getvalue())
        self.assertIn("CORNER DELI", result["raw_text"])
        self.assertIn("20.00", result["raw_text"])
        self.assertEqual(result["merchant"], "CORNER DELI")
        self.assertEqual(result["subtotal_cents"], 1722)
        self.assertEqual(result["date"], "2026-11-25")
        self.assertEqual(result["total_cents"], 1875)
        self.assertEqual(result["tax_cents"], 153)

    def test_unreadable_input(self):
        """Distinguish an unsupported file from damaged PNG data."""
        with tempfile.TemporaryDirectory() as folder:
            image = Path(folder) / "scan.png"
            image.write_bytes(b"plain text")
            with self.assertRaisesRegex(ReceiptOCRError, "PNG or JPEG"):
                extract_text(image)
            image.write_bytes(b"\x89PNG\r\n\x1a\n")
            with self.assertRaisesRegex(ReceiptOCRError, "could not read"):
                extract_text(image)

    def test_missing_image(self):
        """The CLI reports an input error on stderr and exits unsuccessfully."""
        with tempfile.TemporaryDirectory() as folder:
            missing = Path(folder) / "missing.png"
            with patch.object(sys, "argv", ["ocr", str(missing)]):
                with redirect_stderr(io.StringIO()) as output:
                    self.assertEqual(main(), 1)
        self.assertIn("missing.png", output.getvalue())

    def test_missing_or_stalled_engine(self):
        """Give specific guidance when Tesseract cannot run or finish."""
        cases = [
            (FileNotFoundError(), "Install Tesseract"),
            (subprocess.TimeoutExpired("tesseract", 30), "timed out"),
        ]
        for error, message in cases:
            with self.subTest(message=message):
                with patch("receipts.ocr.subprocess.run", side_effect=error):
                    with self.assertRaisesRegex(ReceiptOCRError, message):
                        extract_text(SAMPLE)

    def test_empty_recognition(self):
        """An image with no recognized words has no reviewable draft."""
        result = subprocess.CompletedProcess([], 0, stdout="\n")
        with patch("receipts.ocr.subprocess.run", return_value=result):
            with self.assertRaisesRegex(ReceiptOCRError, "No text recognized"):
                extract_text(SAMPLE)
