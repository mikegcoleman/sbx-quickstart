"""
Pytest fixtures for DevBoard backend tests.

Uses an in-memory SQLite database so tests run without Postgres.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def registered_user(client):
    """Register a test user and return their credentials."""
    resp = client.post(
        "/auth/register",
        json={"email": "alice@example.com", "username": "alice", "password": "secret123"},
    )
    assert resp.status_code == 201
    return {"username": "alice", "password": "secret123", "id": resp.json()["id"]}


@pytest.fixture
def auth_headers(client, registered_user):
    """Return Authorization headers for the test user."""
    resp = client.post(
        "/auth/login",
        data={
            "username": registered_user["username"],
            "password": registered_user["password"],
        },
    )
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def project(client, auth_headers):
    """Create a test project and return its data."""
    resp = client.post(
        "/projects/",
        json={"name": "Test Project", "description": "A project for testing"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    return resp.json()
