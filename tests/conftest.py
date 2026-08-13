import os
import tempfile
import pytest

# Use a fresh temp file-based SQLite DB per test session (in-memory SQLite
# doesn't reliably persist across the separate connections Flask-SQLAlchemy
# opens per request).
_db_fd, _db_path = tempfile.mkstemp(suffix=".db")
os.environ["DATABASE_URL"] = f"sqlite:///{_db_path}"

from app import create_app, db as _db


@pytest.fixture()
def app():
    flask_app = create_app()
    flask_app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    yield flask_app
    with flask_app.app_context():
        _db.session.remove()
        _db.drop_all()
        _db.create_all()  # leave a clean slate for the next test


@pytest.fixture()
def client(app):
    return app.test_client()


def register(client, username, email, password, role):
    return client.post(
        "/auth/register",
        data={
            "username": username,
            "email": email,
            "password": password,
            "confirm_password": password,
            "role": role,
        },
        follow_redirects=True,
    )


def login(client, username, password):
    return client.post(
        "/auth/login",
        data={"username": username, "password": password},
        follow_redirects=True,
    )


def logout(client):
    return client.get("/auth/logout", follow_redirects=True)
