import os

import pytest

os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-with-at-least-32-bytes")

from app import create_app, db
from app.models import User


class TestConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = "test-secret-key-with-at-least-32-bytes"


@pytest.fixture()
def app():
    application = create_app(TestConfig)

    with application.app_context():
        db.create_all()

    yield application

    with application.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def _creer_entetes_authentification(client, email):
    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": "password123"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.get_json()['access_token']}"}


@pytest.fixture()
def client_auth(client):
    response = client.post(
        "/api/auth/register",
        json={
            "username": "client",
            "email": "client@example.com",
            "password": "password123",
        },
    )
    assert response.status_code == 201
    return _creer_entetes_authentification(client, "client@example.com")


@pytest.fixture()
def admin_auth(client, app):
    with app.app_context():
        admin = User(nom="admin", email="admin@example.com", role="admin")
        admin.set_password("password123")
        db.session.add(admin)
        db.session.commit()

    return _creer_entetes_authentification(client, "admin@example.com")


@pytest.fixture()
def second_client_auth(client):
    response = client.post(
        "/api/auth/register",
        json={
            "username": "second_client",
            "email": "second@example.com",
            "password": "password123",
        },
    )
    assert response.status_code == 201
    return _creer_entetes_authentification(client, "second@example.com")