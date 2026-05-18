"""
test_api_auth.py — Integration tests for /api/auth/* endpoints.

Covers:
  - POST /api/auth/register  (happy + sad paths)
  - POST /api/auth/login     (happy + sad paths)
  - GET  /api/auth/me        (authenticated + unauthenticated)
"""

import pytest
from tests.conftest import register_and_approve, get_token, auth_headers


# ── Register ──────────────────────────────────────────────────────────────────

class TestRegister:
    def test_register_success(self, client):
        resp = client.post("/api/auth/register", json={
            "username": "newuser",
            "email": "newuser@test.com",
            "password": "password123",
        })
        assert resp.status_code == 201
        assert "message" in resp.json()

    def test_register_duplicate_username(self, client, db_session):
        register_and_approve(client, db_session, username="dupuser", email="dup1@test.com")
        resp = client.post("/api/auth/register", json={
            "username": "dupuser",
            "email": "other@test.com",
            "password": "password123",
        })
        assert resp.status_code == 400
        assert "already taken" in resp.json()["detail"].lower()

    def test_register_duplicate_email(self, client, db_session):
        register_and_approve(client, db_session, username="emailuser1", email="shared@test.com")
        resp = client.post("/api/auth/register", json={
            "username": "emailuser2",
            "email": "shared@test.com",
            "password": "password123",
        })
        assert resp.status_code == 400
        assert "email" in resp.json()["detail"].lower()

    def test_register_short_username(self, client):
        resp = client.post("/api/auth/register", json={
            "username": "ab",
            "email": "short@test.com",
            "password": "password123",
        })
        assert resp.status_code == 400
        assert "username" in resp.json()["detail"].lower()

    def test_register_short_password(self, client):
        resp = client.post("/api/auth/register", json={
            "username": "validname",
            "email": "valid@test.com",
            "password": "123",
        })
        assert resp.status_code == 400
        assert "password" in resp.json()["detail"].lower()

    def test_register_new_user_is_not_approved(self, client, db_session):
        """Freshly registered users must wait for admin approval."""
        resp = client.post("/api/auth/register", json={
            "username": "pendinguser",
            "email": "pending@test.com",
            "password": "password123",
        })
        assert resp.status_code == 201
        # Attempt login — should be rejected (not approved yet)
        login = client.post("/api/auth/login",
                            data={"username": "pendinguser", "password": "password123"})
        assert login.status_code == 403
        assert "pending" in login.json()["detail"].lower()


# ── Login ─────────────────────────────────────────────────────────────────────

class TestLogin:
    def test_login_approved_user(self, client, db_session):
        register_and_approve(client, db_session, username="approvedlogin",
                             email="approvedlogin@test.com")
        resp = client.post("/api/auth/login",
                           data={"username": "approvedlogin", "password": "password123"})
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["username"] == "approvedlogin"

    def test_login_wrong_password(self, client, db_session):
        register_and_approve(client, db_session, username="wrongpw",
                             email="wrongpw@test.com")
        resp = client.post("/api/auth/login",
                           data={"username": "wrongpw", "password": "notcorrect"})
        assert resp.status_code == 401

    def test_login_nonexistent_user(self, client):
        resp = client.post("/api/auth/login",
                           data={"username": "nobody", "password": "anything"})
        assert resp.status_code == 401

    def test_login_unapproved_user(self, client):
        """Users who registered but have not been approved cannot log in."""
        client.post("/api/auth/register", json={
            "username": "unapproved",
            "email": "unapproved@test.com",
            "password": "password123",
        })
        resp = client.post("/api/auth/login",
                           data={"username": "unapproved", "password": "password123"})
        assert resp.status_code == 403


# ── GET /api/auth/me ──────────────────────────────────────────────────────────

class TestGetMe:
    def test_me_with_valid_token(self, client, db_session):
        register_and_approve(client, db_session, username="meuser",
                             email="meuser@test.com")
        headers = auth_headers(client, username="meuser")
        resp = client.get("/api/auth/me", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "meuser"
        assert data["is_admin"] is False

    def test_me_without_token(self, client):
        resp = client.get("/api/auth/me")
        assert resp.status_code == 401

    def test_me_with_invalid_token(self, client):
        resp = client.get("/api/auth/me",
                          headers={"Authorization": "Bearer this.is.invalid"})
        assert resp.status_code == 401
