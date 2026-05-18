"""
test_api_endpoints.py — Integration tests for core API endpoints.

Covers:
  - GET  /health
  - GET  /api/history
  - DELETE /api/history/{id}
  - POST /api/segment       (ML model mocked)
  - POST /api/segment-batch (ML model mocked)
  - POST /api/export-segment-pdf
"""

import io
import base64
import json
from unittest.mock import patch, MagicMock

import numpy as np
import pytest

from tests.conftest import register_and_approve, auth_headers, make_png_bytes


# ── /health ───────────────────────────────────────────────────────────────────

class TestHealth:
    def test_health_returns_ok(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


# ── /api/history ──────────────────────────────────────────────────────────────

class TestHistory:
    def test_history_requires_auth(self, client):
        resp = client.get("/api/history")
        assert resp.status_code == 401

    def test_history_empty_for_new_user(self, client, db_session):
        register_and_approve(client, db_session, username="histuser",
                             email="histuser@test.com")
        headers = auth_headers(client, username="histuser")
        resp = client.get("/api/history", headers=headers)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_history_delete_nonexistent_record(self, client, db_session):
        register_and_approve(client, db_session, username="deluser",
                             email="deluser@test.com")
        headers = auth_headers(client, username="deluser")
        resp = client.delete("/api/history/99999", headers=headers)
        assert resp.status_code == 404

    def test_history_delete_requires_auth(self, client):
        resp = client.delete("/api/history/1")
        assert resp.status_code == 401


# ── /api/segment ──────────────────────────────────────────────────────────────

# Minimal fake segmentation result (no real model needed)
FAKE_SEG_RESULT = {
    "original":  base64.b64encode(b"fakeimage").decode(),
    "overlay":   base64.b64encode(b"fakeimage").decode(),
    "extracted": base64.b64encode(b"fakeimage").decode(),
    "wall_pct":  12.5,
    "width":     64,
    "height":    64,
}


class TestSegmentEndpoint:
    def test_segment_success(self, client):
        with patch("app.run_segmentation", return_value=FAKE_SEG_RESULT):
            png = make_png_bytes()
            resp = client.post(
                "/api/segment",
                files={"image": ("floor.png", io.BytesIO(png), "image/png")},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "wall_pct" in data

    def test_segment_rejects_non_image(self, client):
        resp = client.post(
            "/api/segment",
            files={"image": ("doc.pdf", io.BytesIO(b"%PDF-1.4"), "application/pdf")},
        )
        assert resp.status_code == 400

    def test_segment_invalid_image_bytes(self, client):
        """Corrupt bytes that OpenCV cannot decode should return an error."""
        with patch("app.run_segmentation", side_effect=ValueError("Cannot decode image")):
            resp = client.post(
                "/api/segment",
                files={"image": ("bad.png", io.BytesIO(b"notanimage"), "image/png")},
            )
        assert resp.status_code in (400, 500)


# ── /api/segment-batch ────────────────────────────────────────────────────────

class TestSegmentBatch:
    def test_batch_no_files_returns_400(self, client, db_session):
        register_and_approve(client, db_session, username="batchuser",
                             email="batchuser@test.com")
        headers = auth_headers(client, username="batchuser")
        resp = client.post("/api/segment-batch", files=[], headers=headers)
        assert resp.status_code in (400, 422)

    def test_batch_with_valid_image(self, client, db_session):
        register_and_approve(client, db_session, username="batchuser2",
                             email="batchuser2@test.com")
        headers = auth_headers(client, username="batchuser2")
        png = make_png_bytes()

        fake_batch_result = {
            "index": 0, "total": 1, "filename": "floor.png",
            "error": None, **FAKE_SEG_RESULT,
        }

        with patch("app.run_segmentation_batch", return_value=iter([fake_batch_result])):
            resp = client.post(
                "/api/segment-batch",
                files=[("images", ("floor.png", io.BytesIO(png), "image/png"))],
                headers=headers,
            )
        assert resp.status_code == 200
        # Response is NDJSON — parse first line
        first_line = resp.text.strip().split("\n")[0]
        data = json.loads(first_line)
        assert data["filename"] == "floor.png"
        assert data["error"] is None


# ── /api/export-segment-pdf ───────────────────────────────────────────────────

class TestExportSegmentPdf:
    def test_export_pdf_success(self, client):
        fake_pdf = b"%PDF-1.4 fake"
        with patch("app.build_segment_pdf_from_b64", return_value=fake_pdf):
            resp = client.post("/api/export-segment-pdf", json={
                "filename":  "floor.png",
                "wall_pct":  "12.5",
                "width":     64,
                "height":    64,
                "original":  base64.b64encode(b"x").decode(),
                "overlay":   base64.b64encode(b"x").decode(),
                "extracted": base64.b64encode(b"x").decode(),
            })
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"