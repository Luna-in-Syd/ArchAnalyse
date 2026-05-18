# ArchAnalyse Backend — Testing Guide

## Overview

This project uses **pytest** for all backend testing. Tests are located in
`backend/tests/` and are organised into five modules covering every layer of
the application.

| File | Scope | Tests |
|---|---|---|
| `test_auth_unit.py` | Unit — auth helpers | 14 |
| `test_api_auth.py` | API integration — register/login/me | 13 |
| `test_api_admin.py` | API integration — admin CRUD | 14 |
| `test_api_endpoints.py` | API integration — core routes | 17 |
| `test_app_utils.py` | Unit — sanitize_filename / save_b64_image | 14 |
| `test_services_wall.py` | Unit — wall comparison algorithms | 20 |
| `test_services_segformer.py` | Unit — segformer utilities + inference | 21 |
| **Total** | | **113** |

---

## Design Decisions

### In-memory Database

All tests use an **in-memory SQLite** database injected via FastAPI's
`dependency_overrides` mechanism. This means:

- Tests never touch the production `archanalyse.db`
- Each test function receives a fresh session that is rolled back after the
  test completes, keeping tests independent
- No test cleanup required

### Mocking the ML Model

Loading the SegFormer model (~100 MB checkpoint + `torch` + `mmseg`) would
make the test suite impractical for CI. Instead, `torch` and `mmseg` are
mocked at the `sys.modules` level *before* any test module is imported. This
lets us test all inference *utilities* (`_binarize`, `_resize_if_large`,
`_encode_png`, `run_segmentation_batch`) and all API endpoints that call the
model, without requiring GPU or model weights.

If you want to run end-to-end model tests, do so separately with the model
mounted and remove the mocks in `conftest.py`.

### Temporary File System

Upload and report directories are redirected to `pytest`'s `tmp_path` fixture.
Generated files are automatically cleaned up by pytest after each test.

---

## Running the Tests

### Prerequisites

```bash
# From the backend/ directory
pip install -r requirements.txt
pip install -r requirements-test.txt
pip install "bcrypt==4.0.1"   # pin for passlib 1.7.4 compatibility
```

> **Note:** If you see `ValueError: password cannot be longer than 72 bytes`
> from passlib, run `pip install "bcrypt==4.0.1"` to fix the bcrypt version
> mismatch.

### Run All Tests

```bash
cd backend/
pytest
```

### Run a Specific Module

```bash
pytest tests/test_api_auth.py
pytest tests/test_services_wall.py
```

### Run with Coverage Report

```bash
pip install pytest-cov
pytest --cov=. --cov-report=term-missing --cov-omit="tests/*,*/__pycache__/*"
```

---

## Coverage Summary

| Layer | Happy Path | Sad Path / Edge Cases | Notes |
|---|---|---|---|
| Password hashing | ✓ | ✓ empty, wrong, differing salts | |
| JWT creation | ✓ | ✓ expired, tampered | |
| User lookup | ✓ | ✓ not found | |
| Register | ✓ | ✓ duplicate username/email, short username/password | |
| Login | ✓ | ✓ wrong password, unapproved, nonexistent | |
| `/api/auth/me` | ✓ | ✓ no token, invalid token | |
| Admin — list pending | ✓ | ✓ non-admin 403, unauth 401 | |
| Admin — list users | ✓ | ✓ non-admin 403 | |
| Admin — approve | ✓ | ✓ 404, already approved, non-admin 403 | |
| Admin — delete | ✓ | ✓ 404, non-admin 403 | |
| `GET /health` | ✓ | — | |
| `GET /api/history` | ✓ | ✓ unauthenticated 401 | |
| `DELETE /api/history/{id}` | ✓ | ✓ 404, unauthenticated 401 | |
| `POST /api/segment` | ✓ (mocked) | ✓ non-image, corrupt bytes | |
| `POST /api/segment-batch` | ✓ (mocked) | ✓ no files | |
| `POST /api/upload` | ✓ (mocked) | ✓ non-PDF, non-image arch/struct | |
| `GET /api/download` | ✓ | ✓ 404, path traversal | |
| `POST /api/export-segment-pdf` | ✓ (mocked) | — | |
| `sanitize_filename` | ✓ | ✓ unsafe chars, path traversal, unicode, empty | |
| `save_b64_image` | ✓ | ✓ overwrites, empty payload | |
| `extract_thick_walls` | ✓ | ✓ all-white input, shape/dtype | |
| `skeletonize` | ✓ | ✓ all-zero input, subset property | |
| `compare_images_thick_walls` | ✓ | ✓ identical images, different sizes | |
| `align_by_walls_mem` | ✓ | ✓ percentile conversion | |
| `_encode_png` | ✓ | ✓ tiny 1×1 image | |
| `_resize_if_large` | ✓ | ✓ small image unchanged, aspect ratio | |
| `_binarize` | ✓ | ✓ bimodal input, dtype | |
| `run_segmentation_batch` | ✓ | ✓ per-item error capture, empty batch | |
