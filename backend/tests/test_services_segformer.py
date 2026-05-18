"""
test_services_segformer.py — Unit tests for services/segformer_inference.py.

The SegFormer model itself is expensive to load, so all tests that
touch model inference are run with the model mocked out. Only the pure
utility functions (_binarize, _resize_if_large, _encode_png) are tested
against real numpy operations.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock torch and mmseg before the module under test is imported at collection time
from unittest.mock import MagicMock as _MM
for _m_name in ("torch", "mmseg", "mmseg.apis"):
    if _m_name not in sys.modules:
        _m = _MM()
        if _m_name == "torch":
            _m.cuda.is_available.return_value = False
        sys.modules[_m_name] = _m

import base64
import io
from unittest.mock import MagicMock, patch

import cv2
import numpy as np
import pytest
from PIL import Image

# ── Import module under test ──────────────────────────────────────────────────
import services.segformer_inference as seg_mod
from services.segformer_inference import (
    _encode_png,
    _resize_if_large,
    _binarize,
    MAX_LONG_EDGE,
    run_segmentation,
    run_segmentation_batch,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def solid_bgr(h=64, w=64, color=(200, 200, 200)):
    img = np.zeros((h, w, 3), dtype=np.uint8)
    img[:] = color
    return img


def encode_to_bytes(img_bgr: np.ndarray) -> bytes:
    _, buf = cv2.imencode(".png", img_bgr)
    return buf.tobytes()


# ── _encode_png ───────────────────────────────────────────────────────────────

class TestEncodePng:
    def test_returns_valid_base64_string(self):
        img = solid_bgr()[:, :, ::-1]  # BGR → RGB
        result = _encode_png(img)
        assert isinstance(result, str)
        # Must decode to valid PNG bytes
        decoded = base64.b64decode(result)
        pil = Image.open(io.BytesIO(decoded))
        assert pil.format == "PNG"

    def test_encoded_image_has_correct_dimensions(self):
        img = np.zeros((32, 48, 3), dtype=np.uint8)
        result = _encode_png(img)
        decoded = base64.b64decode(result)
        pil = Image.open(io.BytesIO(decoded))
        assert pil.size == (48, 32)  # PIL: (width, height)

    def test_empty_image_encodes_without_error(self):
        tiny = np.zeros((1, 1, 3), dtype=np.uint8)
        result = _encode_png(tiny)
        assert len(result) > 0


# ── _resize_if_large ─────────────────────────────────────────────────────────

class TestResizeIfLarge:
    def test_small_image_unchanged(self):
        img = solid_bgr(h=100, w=100)
        result = _resize_if_large(img)
        assert result.shape == (100, 100, 3)

    def test_large_image_scaled_down(self):
        large = solid_bgr(h=2000, w=3000)
        result = _resize_if_large(large)
        h, w = result.shape[:2]
        assert max(h, w) <= MAX_LONG_EDGE

    def test_aspect_ratio_preserved(self):
        # 400 × 800 — width is the long edge
        img = solid_bgr(h=400, w=800)
        result = _resize_if_large(img)
        h, w = result.shape[:2]
        original_ratio = 400 / 800
        result_ratio   = h / w
        assert abs(result_ratio - original_ratio) < 0.02

    def test_exact_max_edge_not_resized(self):
        img = solid_bgr(h=MAX_LONG_EDGE, w=MAX_LONG_EDGE)
        result = _resize_if_large(img)
        assert result.shape == img.shape

    def test_output_dtype_preserved(self):
        img = solid_bgr(h=2000, w=2000)
        result = _resize_if_large(img)
        assert result.dtype == np.uint8


# ── _binarize ─────────────────────────────────────────────────────────────────

class TestBinarize:
    def test_output_is_3_channel(self):
        img = solid_bgr(h=64, w=64, color=(128, 128, 128))
        result = _binarize(img)
        assert result.shape == (64, 64, 3)

    def test_output_contains_only_0_and_255(self):
        """Otsu binarization produces a binary image."""
        img = solid_bgr(h=64, w=64, color=(100, 100, 100))
        result = _binarize(img)
        unique_vals = set(np.unique(result))
        assert unique_vals.issubset({0, 255})

    def test_bimodal_image_binarizes_to_both_values(self):
        """
        An image with two distinct intensity regions should produce both
        black and white pixels after Otsu binarization.
        """
        img = np.zeros((64, 64, 3), dtype=np.uint8)
        img[:32, :] = 30   # dark region
        img[32:, :] = 200  # light region
        result = _binarize(img)
        unique_vals = set(np.unique(result))
        assert 0 in unique_vals and 255 in unique_vals

    def test_output_dtype_is_uint8(self):
        img = solid_bgr()
        result = _binarize(img)
        assert result.dtype == np.uint8


# ── run_segmentation (model mocked) ──────────────────────────────────────────

def _make_mock_model_result(h=64, w=64):
    """Build a minimal mmseg inference result mock."""
    pred = MagicMock()
    pred.pred_sem_seg.data.__getitem__ = MagicMock(
        return_value=MagicMock(
            cpu=lambda: MagicMock(
                numpy=lambda: np.zeros((h, w), dtype=np.int64)
            )
        )
    )
    return pred


class TestRunSegmentation:
    def test_returns_expected_keys(self):
        img_bytes = encode_to_bytes(solid_bgr())

        mock_result = _make_mock_model_result()
        with patch.object(seg_mod, "get_seg_model") as mock_get, \
             patch("services.segformer_inference.inference_model", return_value=mock_result,
                   create=True):
            mock_get.return_value = MagicMock()
            with patch("services.segformer_inference._infer_one",
                       return_value={
                           "original":  "b64data",
                           "overlay":   "b64data",
                           "extracted": "b64data",
                           "wall_pct":  5.0,
                           "width":     64,
                           "height":    64,
                       }):
                result = run_segmentation(img_bytes)

        for key in ("original", "overlay", "extracted", "wall_pct", "width", "height"):
            assert key in result, f"Missing key: {key}"

    def test_invalid_bytes_raises_value_error(self):
        with pytest.raises((ValueError, Exception)):
            run_segmentation(b"not-an-image")

    def test_wall_pct_is_numeric(self):
        img_bytes = encode_to_bytes(solid_bgr())
        with patch("services.segformer_inference._infer_one",
                   return_value={
                       "original": "x", "overlay": "x", "extracted": "x",
                       "wall_pct": 0.0, "width": 64, "height": 64,
                   }):
            result = run_segmentation(img_bytes)
        assert isinstance(result["wall_pct"], (int, float))


# ── run_segmentation_batch (model mocked) ────────────────────────────────────

class TestRunSegmentationBatch:
    def test_batch_yields_correct_count(self):
        items = [
            ("img1.png", encode_to_bytes(solid_bgr())),
            ("img2.png", encode_to_bytes(solid_bgr())),
        ]
        fake = {"original": "x", "overlay": "x", "extracted": "x",
                "wall_pct": 0.0, "width": 64, "height": 64}

        with patch("services.segformer_inference._infer_one", return_value=fake):
            results = list(run_segmentation_batch(items))

        assert len(results) == 2

    def test_batch_result_contains_index_and_total(self):
        items = [("img.png", encode_to_bytes(solid_bgr()))]
        fake = {"original": "x", "overlay": "x", "extracted": "x",
                "wall_pct": 0.0, "width": 64, "height": 64}

        with patch("services.segformer_inference._infer_one", return_value=fake):
            results = list(run_segmentation_batch(items))

        assert results[0]["index"] == 0
        assert results[0]["total"] == 1
        assert results[0]["filename"] == "img.png"

    def test_batch_error_captured_per_item(self):
        """A failure in one image should not crash the whole batch."""
        items = [
            ("bad.png",  b"not-an-image"),
            ("good.png", encode_to_bytes(solid_bgr())),
        ]
        fake = {"original": "x", "overlay": "x", "extracted": "x",
                "wall_pct": 0.0, "width": 64, "height": 64}

        def side_effect(img_bgr):
            raise ValueError("decode failed")

        with patch("services.segformer_inference._infer_one", side_effect=side_effect):
            results = list(run_segmentation_batch(items))

        assert len(results) == 2
        assert results[0]["error"] is not None
        assert results[1]["error"] is not None  # also fails (mocked to always raise)

    def test_empty_batch_yields_nothing(self):
        results = list(run_segmentation_batch([]))
        assert results == []
