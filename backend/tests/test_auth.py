"""Tests for authentication endpoints."""


def test_register_new_user(client):
    resp = client.post(
        "/auth/register",
        json={"email": "bob@example.com", "username": "bob", "password": "pass1234"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "bob@example.com"
    assert data["username"] == "bob"
    assert "hashed_password" not in data


def test_register_duplicate_email(client, registered_user):
    resp = client.post(
        "/auth/register",
        json={
            "email": "alice@example.com",
            "username": "alice2",
            "password": "other",
        },
    )
    assert resp.status_code == 400
    assert "Email already registered" in resp.json()["detail"]


def test_register_duplicate_username(client, registered_user):
    resp = client.post(
        "/auth/register",
        json={
            "email": "alice2@example.com",
            "username": "alice",
            "password": "other",
        },
    )
    assert resp.status_code == 400
    assert "Username already taken" in resp.json()["detail"]


def test_login_success(client, registered_user):
    resp = client.post(
        "/auth/login",
        data={"username": "alice", "password": "secret123"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client, registered_user):
    resp = client.post(
        "/auth/login",
        data={"username": "alice", "password": "wrong"},
    )
    assert resp.status_code == 401


def test_get_current_user(client, auth_headers):
    resp = client.get("/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["username"] == "alice"


def test_get_current_user_unauthenticated(client):
    resp = client.get("/auth/me")
    assert resp.status_code == 401
