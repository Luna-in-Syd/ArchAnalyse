"""
conftest.py — Shared fixtures for all ArchAnalyse backend tests.

Uses an in-memory SQLite database so tests are fully isolated and
never touch the production archanalyse.db file.
"""

import sys
import os
import io
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# ── Add backend directory to path ────────────────────────────────────────────
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# ── Mock heavy ML dependencies BEFORE importing app ──────────────────────────
# This prevents mmseg / torch model from being loaded during testing.
mock_mmseg = MagicMock()
sys.modules.setdefault("mmseg", mock_mmseg)
sys.modules.setdefault("mmseg.apis", mock_mmseg.apis)

# Mock torch so segformer_inference.py can be imported without a GPU/torch install
mock_torch = MagicMock()
mock_torch.cuda.is_available.return_value = False
mock_torch.load = MagicMock()
sys.modules.setdefault("torch", mock_torch)

# ── In-memory test database ───────────────────────────────────────────────────
TEST_DB_URL = "sqlite:///:memory:"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def _patch_db_engine():
    """
    Replace the production database engine with an in-memory engine for the
    entire test session. Runs before any test imports app internals.
    """
    import database as db_module
    db_module.engine = test_engine
    db_module.SessionLocal = TestingSessionLocal
    from models import Base  # noqa: F401 — triggers table creation
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture()
def db_session():
    """
    Yield a fresh database session for each test and roll back afterwards,
    keeping tests independent.
    """
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db_session, tmp_path):
    """
    FastAPI TestClient backed by the in-memory database and a temporary
    filesystem so uploads/reports never pollute the working directory.
    """
    import database as db_module
    from app import app

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[db_module.get_db] = override_get_db

    # Redirect upload/report directories to tmp_path
    import app as app_module
    app_module.UPLOAD_DIR = tmp_path / "uploads"
    app_module.REPORT_DIR = tmp_path / "reports"
    app_module.TMP_DIR    = tmp_path / "tmp_reports"
    app_module.HISTORY_DIR = tmp_path / "history_images"
    for d in (app_module.UPLOAD_DIR, app_module.REPORT_DIR,
              app_module.TMP_DIR, app_module.HISTORY_DIR):
        d.mkdir(parents=True, exist_ok=True)

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_png_bytes(width: int = 64, height: int = 64) -> bytes:
    """Return minimal valid PNG bytes (white image)."""
    import numpy as np
    import cv2
    img = np.ones((height, width, 3), dtype=np.uint8) * 255
    _, buf = cv2.imencode(".png", img)
    return buf.tobytes()


def register_and_approve(client, db_session, username="testuser",
                          password="password123", email=None):
    """
    Register a new user and immediately approve them, then return credentials.
    """
    from auth import get_password_hash
    from models import User

    if email is None:
        email = f"{username}@test.com"

    user = User(
        username=username,
        email=email,
        hashed_password=get_password_hash(password),
        is_admin=False,
        is_approved=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def get_token(client, username="testuser", password="password123"):
    """Login and return a Bearer token string."""
    resp = client.post(
        "/api/auth/login",
        data={"username": username, "password": password},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def auth_headers(client, username="testuser", password="password123"):
    """Return Authorization header dict for authenticated requests."""
    return {"Authorization": f"Bearer {get_token(client, username, password)}"}


def make_admin(db_session, username="admin_test", password="adminpass",
               email="admin_test@test.com"):
    """Create an admin user directly in the DB."""
    from auth import get_password_hash
    from models import User

    user = User(
        username=username,
        email=email,
        hashed_password=get_password_hash(password),
        is_admin=True,
        is_approved=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user
