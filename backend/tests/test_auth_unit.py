"""
test_auth_unit.py — Unit tests for auth.py utility functions.

Tests password hashing, JWT token creation/decoding, and the
authenticate_user / get_user_by_* helpers in complete isolation
(no HTTP layer, no real database state leaked between tests).
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



from datetime import timedelta

import pytest
from jose import jwt

import auth as auth_module
from auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_user_by_username,
    get_user_by_email,
    authenticate_user,
    SECRET_KEY,
    ALGORITHM,
)


# ── Password utilities ────────────────────────────────────────────────────────

class TestPasswordHashing:
    def test_hash_is_not_plaintext(self):
        hashed = get_password_hash("secret")
        assert hashed != "secret"

    def test_verify_correct_password(self):
        hashed = get_password_hash("mypassword")
        assert verify_password("mypassword", hashed) is True

    def test_verify_wrong_password(self):
        hashed = get_password_hash("mypassword")
        assert verify_password("wrongpassword", hashed) is False

    def test_two_hashes_of_same_password_differ(self):
        """bcrypt uses a random salt — hashes should not be identical."""
        h1 = get_password_hash("same")
        h2 = get_password_hash("same")
        assert h1 != h2

    def test_empty_password_can_be_hashed_and_verified(self):
        hashed = get_password_hash("")
        assert verify_password("", hashed) is True
        assert verify_password("not-empty", hashed) is False


# ── JWT token creation ────────────────────────────────────────────────────────

class TestCreateAccessToken:
    def test_token_is_valid_jwt(self):
        token = create_access_token({"sub": "luna"})
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "luna"

    def test_token_contains_expiry(self):
        token = create_access_token({"sub": "luna"})
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert "exp" in payload

    def test_custom_expiry_delta(self):
        """Token with 1-minute delta should expire sooner than default."""
        token = create_access_token({"sub": "luna"}, expires_delta=timedelta(minutes=1))
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "luna"

    def test_expired_token_raises(self):
        token = create_access_token(
            {"sub": "luna"}, expires_delta=timedelta(seconds=-1)
        )
        with pytest.raises(Exception):  # jose.ExpiredSignatureError is a subclass
            jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

    def test_tampered_token_raises(self):
        token = create_access_token({"sub": "luna"})
        tampered = token[:-5] + "XXXXX"
        with pytest.raises(Exception):
            jwt.decode(tampered, SECRET_KEY, algorithms=[ALGORITHM])


# ── Database-backed helpers ───────────────────────────────────────────────────

class TestGetUserHelpers:
    def test_get_user_by_username_found(self, db_session):
        from models import User
        user = User(
            username="findme",
            email="findme@test.com",
            hashed_password=get_password_hash("pass"),
            is_admin=False,
            is_approved=True,
        )
        db_session.add(user)
        db_session.commit()

        result = get_user_by_username(db_session, "findme")
        assert result is not None
        assert result.username == "findme"

    def test_get_user_by_username_not_found(self, db_session):
        result = get_user_by_username(db_session, "nobody")
        assert result is None

    def test_get_user_by_email_found(self, db_session):
        from models import User
        user = User(
            username="emailuser",
            email="unique@test.com",
            hashed_password=get_password_hash("pass"),
            is_admin=False,
            is_approved=True,
        )
        db_session.add(user)
        db_session.commit()

        result = get_user_by_email(db_session, "unique@test.com")
        assert result is not None
        assert result.email == "unique@test.com"

    def test_get_user_by_email_not_found(self, db_session):
        result = get_user_by_email(db_session, "ghost@test.com")
        assert result is None


class TestAuthenticateUser:
    def test_correct_credentials(self, db_session):
        from models import User
        user = User(
            username="authuser",
            email="authuser@test.com",
            hashed_password=get_password_hash("correct"),
            is_admin=False,
            is_approved=True,
        )
        db_session.add(user)
        db_session.commit()

        result = authenticate_user(db_session, "authuser", "correct")
        assert result is not None
        assert result.username == "authuser"

    def test_wrong_password(self, db_session):
        from models import User
        user = User(
            username="badpassuser",
            email="badpass@test.com",
            hashed_password=get_password_hash("correct"),
            is_admin=False,
            is_approved=True,
        )
        db_session.add(user)
        db_session.commit()

        result = authenticate_user(db_session, "badpassuser", "wrong")
        assert result is None

    def test_nonexistent_user(self, db_session):
        result = authenticate_user(db_session, "ghost", "anypassword")
        assert result is None
