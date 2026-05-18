"""
test_api_admin.py — Integration tests for /api/admin/* endpoints.

Covers:
  - GET  /api/admin/pending
  - GET  /api/admin/users
  - POST /api/admin/approve/{user_id}
  - DELETE /api/admin/users/{user_id}

All endpoints require admin authentication; tests verify that
non-admins are rejected with 403.
"""

import pytest
from tests.conftest import register_and_approve, make_admin, auth_headers


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture()
def admin_headers(client, db_session):
    make_admin(db_session, username="sysadmin", password="adminpass",
               email="sysadmin@test.com")
    return auth_headers(client, username="sysadmin", password="adminpass")


@pytest.fixture()
def regular_headers(client, db_session):
    register_and_approve(client, db_session, username="regular",
                         email="regular@test.com")
    return auth_headers(client, username="regular")


# ── GET /api/admin/pending ────────────────────────────────────────────────────

class TestListPendingUsers:
    def test_admin_can_see_pending_users(self, client, db_session, admin_headers):
        # Register a user without approving them
        client.post("/api/auth/register", json={
            "username": "pendingone",
            "email": "pendingone@test.com",
            "password": "password123",
        })
        resp = client.get("/api/admin/pending", headers=admin_headers)
        assert resp.status_code == 200
        usernames = [u["username"] for u in resp.json()]
        assert "pendingone" in usernames

    def test_non_admin_gets_403(self, client, regular_headers):
        resp = client.get("/api/admin/pending", headers=regular_headers)
        assert resp.status_code == 403

    def test_unauthenticated_gets_401(self, client):
        resp = client.get("/api/admin/pending")
        assert resp.status_code == 401

    def test_approved_users_not_in_pending(self, client, db_session, admin_headers):
        register_and_approve(client, db_session, username="already_approved",
                             email="approved@test.com")
        resp = client.get("/api/admin/pending", headers=admin_headers)
        assert resp.status_code == 200
        usernames = [u["username"] for u in resp.json()]
        assert "already_approved" not in usernames


# ── GET /api/admin/users ──────────────────────────────────────────────────────

class TestListAllUsers:
    def test_admin_sees_all_non_admin_users(self, client, db_session, admin_headers):
        register_and_approve(client, db_session, username="user_a",
                             email="usera@test.com")
        resp = client.get("/api/admin/users", headers=admin_headers)
        assert resp.status_code == 200
        usernames = [u["username"] for u in resp.json()]
        assert "user_a" in usernames

    def test_admin_is_not_listed(self, client, admin_headers):
        """Admins should not appear in the user list."""
        resp = client.get("/api/admin/users", headers=admin_headers)
        assert resp.status_code == 200
        usernames = [u["username"] for u in resp.json()]
        assert "sysadmin" not in usernames

    def test_non_admin_gets_403(self, client, regular_headers):
        resp = client.get("/api/admin/users", headers=regular_headers)
        assert resp.status_code == 403


# ── POST /api/admin/approve/{user_id} ────────────────────────────────────────

class TestApproveUser:
    def test_admin_can_approve_pending_user(self, client, db_session, admin_headers):
        client.post("/api/auth/register", json={
            "username": "toapprove",
            "email": "toapprove@test.com",
            "password": "password123",
        })
        # Find user id
        pending = client.get("/api/admin/pending", headers=admin_headers).json()
        user_id = next(u["id"] for u in pending if u["username"] == "toapprove")

        resp = client.post(f"/api/admin/approve/{user_id}", headers=admin_headers)
        assert resp.status_code == 200
        assert "approved" in resp.json()["message"].lower()

        # User can now log in
        login = client.post("/api/auth/login",
                            data={"username": "toapprove", "password": "password123"})
        assert login.status_code == 200

    def test_approve_nonexistent_user(self, client, admin_headers):
        resp = client.post("/api/admin/approve/99999", headers=admin_headers)
        assert resp.status_code == 404

    def test_approve_already_approved_user(self, client, db_session, admin_headers):
        register_and_approve(client, db_session, username="alreadyok",
                             email="alreadyok@test.com")
        users = client.get("/api/admin/users", headers=admin_headers).json()
        user_id = next(u["id"] for u in users if u["username"] == "alreadyok")

        resp = client.post(f"/api/admin/approve/{user_id}", headers=admin_headers)
        assert resp.status_code == 400

    def test_non_admin_cannot_approve(self, client, db_session, regular_headers):
        resp = client.post("/api/admin/approve/1", headers=regular_headers)
        assert resp.status_code == 403


# ── DELETE /api/admin/users/{user_id} ────────────────────────────────────────

class TestDeleteUser:
    def test_admin_can_delete_user(self, client, db_session, admin_headers):
        register_and_approve(client, db_session, username="todelete",
                             email="todelete@test.com")
        users = client.get("/api/admin/users", headers=admin_headers).json()
        user_id = next(u["id"] for u in users if u["username"] == "todelete")

        resp = client.delete(f"/api/admin/users/{user_id}", headers=admin_headers)
        assert resp.status_code == 200

        # User should no longer appear
        users_after = client.get("/api/admin/users", headers=admin_headers).json()
        usernames_after = [u["username"] for u in users_after]
        assert "todelete" not in usernames_after

    def test_delete_nonexistent_user(self, client, admin_headers):
        resp = client.delete("/api/admin/users/99999", headers=admin_headers)
        assert resp.status_code == 404

    def test_non_admin_cannot_delete(self, client, regular_headers):
        resp = client.delete("/api/admin/users/1", headers=regular_headers)
        assert resp.status_code == 403
