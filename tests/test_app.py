"""Smoke tests for RunStudio Flask app."""

from __future__ import annotations

import pytest

from app import create_app


@pytest.fixture
def client():
    app = create_app({"TESTING": True, "DATABASE": ":memory:", "SECRET_KEY": "test"})
    with app.test_client() as c:
        yield c


def test_index(client):
    assert client.get("/").status_code == 200


def test_execute_python(client):
    r = client.post("/execute", json={"code": "print(2+2)", "language": "python"})
    assert r.status_code == 200
    data = r.get_json()
    assert data["stdout"] == "4\n"
    assert data["stderr"] == ""


def test_execute_bad_language(client):
    r = client.post("/execute", json={"code": "x", "language": "ruby"})
    assert r.status_code == 400


def test_scripts_require_login(client):
    assert client.get("/api/scripts").status_code == 302


def test_register_execute_scripts(client):
    client.post(
        "/register",
        data={
            "username": "alice",
            "password": "secret",
            "confirm_password": "secret",
        },
        follow_redirects=True,
    )
    r = client.post("/execute", json={"code": 'print("hi")', "language": "python"})
    assert r.status_code == 200
    assert "hi" in r.get_json()["stdout"]

    r = client.post(
        "/api/scripts",
        json={"title": "T1", "code": "x=1", "language": "python"},
    )
    assert r.status_code == 201
    sid = r.get_json()["id"]

    r = client.get("/api/scripts")
    assert r.status_code == 200
    assert len(r.get_json()["scripts"]) == 1

    r = client.get(f"/api/scripts/{sid}")
    assert r.status_code == 200
    assert r.get_json()["code"] == "x=1"


def test_login_rejects_external_next(client):
    client.post(
        "/register",
        data={
            "username": "bob",
            "password": "secret",
            "confirm_password": "secret",
        },
        follow_redirects=True,
    )
    client.post("/logout", follow_redirects=True)
    r = client.post(
        "/login?next=http://evil.com",
        data={"username": "bob", "password": "secret"},
        follow_redirects=False,
    )
    assert r.status_code == 302
    assert r.headers["Location"].endswith("/")
    assert "evil.com" not in r.headers["Location"]
