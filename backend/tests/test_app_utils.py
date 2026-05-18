"""
test_app_utils.py — Unit tests for utility functions defined in app.py.

sanitize_filename and save_b64_image are tested independently of the
HTTP layer; they are pure or near-pure functions that are straightforward
to unit-test.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from unittest.mock import MagicMock as _MM
for _m_name in ("torch", "mmseg", "mmseg.apis"):
    if _m_name not in sys.modules:
        _m = _MM()
        if _m_name == "torch":
            _m.cuda.is_available.return_value = False
        sys.modules[_m_name] = _m



import base64
import tempfile
from pathlib import Path

import pytest

from app import sanitize_filename, save_b64_image


# ── sanitize_filename ─────────────────────────────────────────────────────────

class TestSanitizeFilename:
    def test_normal_filename_unchanged(self):
        assert sanitize_filename("floor_plan.pdf") == "floor_plan.pdf"

    def test_spaces_removed(self):
        result = sanitize_filename("my floor plan.pdf")
        assert " " not in result

    def test_path_traversal_stripped(self):
        """
        Path traversal sequences must not survive sanitization:
        sanitize_filename strips / and \ so the result cannot escape the
        intended directory, even though dots are kept as they are allowed.
        The important invariant is the absence of directory separators.
        """
        result = sanitize_filename("../../etc/passwd")
        assert "/" not in result
        assert "\\" not in result

    def test_unicode_non_ascii_stripped(self):
        result = sanitize_filename("平面图.pdf")
        # Chinese characters are not in SAFE_CHARS — should be stripped
        for ch in "平面图":
            assert ch not in result

    def test_empty_string_returns_default(self):
        assert sanitize_filename("", default="upload.pdf") == "upload.pdf"

    def test_only_unsafe_chars_returns_default(self):
        result = sanitize_filename("!!!@@@###", default="fallback.pdf")
        assert result == "fallback.pdf"

    def test_allowed_chars_kept(self):
        allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-"
        result = sanitize_filename(allowed)
        assert result == allowed

    def test_mixed_keeps_safe_portion(self):
        result = sanitize_filename("file name (1).pdf")
        # Parentheses and spaces stripped, letters and dot kept
        assert "(" not in result
        assert " " not in result
        assert "filename1.pdf" == result or "filename1" in result

    def test_default_parameter_used_when_name_all_unsafe(self):
        # Angle brackets are stripped; alphanumeric chars inside them survive.
        # If the remaining safe characters are non-empty, they are returned.
        result = sanitize_filename("!!!@@@###", default="safe.pdf")
        assert result == "safe.pdf"  # no safe chars at all → fallback


# ── save_b64_image ────────────────────────────────────────────────────────────

class TestSaveB64Image:
    def _make_b64(self, content: bytes = b"fake png bytes") -> str:
        return base64.b64encode(content).decode()

    def test_file_created_at_destination(self, tmp_path):
        dest = tmp_path / "output.png"
        save_b64_image(self._make_b64(), dest)
        assert dest.exists()

    def test_file_contents_match_decoded_bytes(self, tmp_path):
        payload = b"this is the image"
        b64 = self._make_b64(payload)
        dest = tmp_path / "test.png"
        save_b64_image(b64, dest)
        assert dest.read_bytes() == payload

    def test_returns_destination_filename(self, tmp_path):
        dest = tmp_path / "result.png"
        returned = save_b64_image(self._make_b64(), dest)
        assert returned == "result.png"

    def test_overwrites_existing_file(self, tmp_path):
        dest = tmp_path / "overwrite.png"
        dest.write_bytes(b"old content")
        save_b64_image(self._make_b64(b"new content"), dest)
        assert dest.read_bytes() == b"new content"

    def test_empty_payload(self, tmp_path):
        dest = tmp_path / "empty.png"
        save_b64_image(self._make_b64(b""), dest)
        assert dest.exists()
        assert dest.read_bytes() == b""
