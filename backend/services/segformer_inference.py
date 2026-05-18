"""
services/segformer_inference.py
SegFormer wall segmentation — single + batch inference.
"""

import base64
import io
import os
from typing import List, Tuple

import cv2
import numpy as np
from PIL import Image

import torch
_original_load = torch.load
def _patched_load(f, map_location=None, **kwargs):
    kwargs['weights_only'] = False
    return _original_load(f, map_location=map_location, **kwargs)
torch.load = _patched_load
# ── Model paths ───────────────────────────────────────────────────────────────
SEG_CONFIG = os.environ.get(
    "SEG_CONFIG",
    "./segformer_b2_wall.py",
)
SEG_CHECKPOINT = os.environ.get(
    "SEG_CHECKPOINT",
    "./best_mIoU_iter.pth",
)
SEG_DEVICE = os.environ.get("SEG_DEVICE", "cuda:0")
MAX_LONG_EDGE = 1024

_seg_model = None


def get_seg_model():
    global _seg_model
    if _seg_model is None:
        from mmseg.apis import init_model
        import torch
        device = "cuda:0" if torch.cuda.is_available() else "cpu"
        print(f"[SegFormer] Loading {SEG_CHECKPOINT} on {device}")
        _seg_model = init_model(SEG_CONFIG, SEG_CHECKPOINT, device=device)
        print("[SegFormer] Model ready")
    return _seg_model


def _encode_png(img_rgb: np.ndarray) -> str:
    buf = io.BytesIO()
    Image.fromarray(img_rgb.astype(np.uint8)).save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def _resize_if_large(img_bgr: np.ndarray) -> np.ndarray:
    h, w = img_bgr.shape[:2]
    if max(h, w) > MAX_LONG_EDGE:
        scale = MAX_LONG_EDGE / max(h, w)
        img_bgr = cv2.resize(img_bgr, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
    return img_bgr


def _binarize(img_bgr: np.ndarray) -> np.ndarray:
    """
    Convert BGR image to black-and-white binary image (3-channel BGR),
    matching the format used during training.

    Pipeline:
      1. Grayscale
      2. Otsu threshold  — automatically finds the best threshold value,
         handles different scan qualities without a fixed number
      3. Convert back to 3-channel BGR so SegFormer's data preprocessor
         (which expects 3 channels) works without any changes
    """
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)


def _infer_one(img_bgr: np.ndarray) -> dict:
    from mmseg.apis import inference_model

    # Keep original for visualisation BEFORE binarization
    img_bgr_orig = _resize_if_large(img_bgr)
    h, w         = img_bgr_orig.shape[:2]
    img_rgb_orig = cv2.cvtColor(img_bgr_orig, cv2.COLOR_BGR2RGB)

    # Binarize for inference
    img_bgr_bin = _binarize(img_bgr_orig)

    model     = get_seg_model()
    result    = inference_model(model, img_bgr_bin)
    pred      = result.pred_sem_seg.data[0].cpu().numpy()
    wall_mask = (pred == 1).astype(np.uint8)

    # Overlay on the ORIGINAL colour image
    ov = img_rgb_orig.copy()
    ov[wall_mask == 1] = [220, 60, 60]
    blended = cv2.addWeighted(img_rgb_orig, 0.55, ov, 0.45, 0)

    mask_r = cv2.resize(wall_mask, (w, h), interpolation=cv2.INTER_NEAREST)
    extracted = np.ones((h, w, 3), dtype=np.uint8) * 255
    extracted[mask_r == 1] = img_rgb_orig[mask_r == 1]

    return {
        "original":  _encode_png(img_rgb_orig),
        "overlay":   _encode_png(blended),
        "extracted": _encode_png(extracted),
        "wall_pct":  round(float(wall_mask.mean() * 100), 1),
        "width":     w,
        "height":    h,
    }


def run_segmentation(image_bytes: bytes) -> dict:
    nparr   = np.frombuffer(image_bytes, np.uint8)
    img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img_bgr is None:
        raise ValueError("Cannot decode image")
    return _infer_one(img_bgr)


def run_segmentation_batch(items: List[Tuple[str, bytes]]):
    """
    Generator: yields one result dict per image in order.
    items: list of (filename, image_bytes)
    """
    total = len(items)
    for i, (filename, image_bytes) in enumerate(items):
        try:
            nparr   = np.frombuffer(image_bytes, np.uint8)
            img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img_bgr is None:
                raise ValueError("Cannot decode image")
            result = _infer_one(img_bgr)
            yield {"index": i, "total": total, "filename": filename, "error": None, **result}
        except Exception as e:
            yield {"index": i, "total": total, "filename": filename, "error": str(e)}