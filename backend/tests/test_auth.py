import re
import time
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from homenet import auth
from homenet.app import create_app

NOW = datetime(2026, 11, 5, 22, 0)
PUBLIC = {"/api/health", "/api/auth/login", "/api/auth/logout"}


@pytest.fixture()
def app():
    auth.reset_failures()
    a = create_app(":memory:", clock=lambda: NOW, background=False)
    a.state.runtime.start()
    a.state.runtime.tick()
    yield a
    auth.reset_failures()


def login(c, username="demo", password="demo"):
    return c.post("/api/auth/login", json={"username": username, "password": password})


def protected_routes(app):
    """Every /api route the app publishes (read from its OpenAPI description)."""
    for path, ops in app.openapi()["paths"].items():
        if path.startswith("/api") and path not in PUBLIC:
            for method in ops:
                yield method.upper(), re.sub(r"\{[^}]+\}", "1", path)


def test_every_endpoint_refuses_without_login(app):
    c = TestClient(app)
    routes = list(protected_routes(app))
    assert len(routes) >= 20
    for method, path in routes:
        r = c.request(method, path, json={})
        assert r.status_code == 401, (method, path, r.status_code)


def test_health_is_public(app):
    assert TestClient(app).get("/api/health").status_code == 200


def test_login_cookie_flags_and_me(app):
    c = TestClient(app)
    r = login(c)
    assert r.status_code == 200 and r.json()["parent"]["display_name"] == "Mom"
    cookie = r.headers["set-cookie"]
    assert "HttpOnly" in cookie and "SameSite=strict" in cookie.replace("Strict", "strict")
    assert "Max-Age" not in cookie and "expires" not in cookie.lower()      # ends with the browser (D20)
    assert c.get("/api/auth/me").json()["parent"]["username"] == "demo"
    r = c.get("/api/overview")                       # logged in, but the child has not been told yet
    assert r.status_code == 403 and r.json()["detail"]["code"] == "consent_required"
    assert c.post("/api/consent", json={"told_child": True}).status_code == 200
    assert c.get("/api/overview").status_code == 200


def test_dad_demo_login(app):
    c = TestClient(app)
    assert login(c, "dad", "demo").json()["parent"]["display_name"] == "Dad"


def test_wrong_password_and_unknown_user_get_the_same_answer(app):
    c = TestClient(app)
    a, b = login(c, "demo", "nope"), login(c, "nobody", "nope")
    assert a.status_code == b.status_code == 401
    assert a.json() == b.json() == {"detail": "Wrong username or password"}
    assert c.get("/api/overview").status_code == 401


def test_five_wrong_passwords_lock_for_a_minute(app):
    c = TestClient(app)
    for _ in range(5):
        assert login(c, "demo", "wrong").status_code == 401
    assert login(c, "demo", "demo").status_code == 429            # even the right one, for 1 minute
    # a minute later it works again
    conn = app.state.runtime.conn
    with pytest.raises(PermissionError):
        auth.login(conn, "demo", "demo", now=time.time() + 30)
    assert auth.login(conn, "demo", "demo", now=time.time() + 61)


def test_passwords_are_stored_hashed(app):
    rows = app.state.runtime.conn.execute("SELECT password_hash FROM parents").fetchall()
    assert rows and all(r[0].startswith("$argon2") and "demo" not in r[0] for r in rows)
    tokens = app.state.runtime.conn.execute("SELECT token_hash FROM sessions").fetchall()
    c = TestClient(app)
    token = login(c).cookies.get(auth.COOKIE)
    stored = [r[0] for r in app.state.runtime.conn.execute("SELECT token_hash FROM sessions")]
    assert token not in stored and len(stored) == len(tokens) + 1


def test_third_parent_refused(app):
    c = TestClient(app)
    login(c)
    r = c.post("/api/auth/parents", json={"username": "gran", "display_name": "Gran", "password": "long-enough"})
    assert r.status_code == 409
    assert c.get("/api/auth/parents").json()["max"] == 2


def test_logout_ends_the_session(app):
    c = TestClient(app)
    token = login(c).cookies.get(auth.COOKIE)
    assert c.post("/api/auth/logout").status_code == 200
    c.cookies.set(auth.COOKIE, token)                       # even replaying the old cookie
    assert c.get("/api/overview").status_code == 401


def test_idle_session_expires_after_8_hours(app):
    conn = app.state.runtime.conn
    t0 = time.time()
    token = auth.login(conn, "demo", "demo", now=t0)
    assert auth.parent_for_token(conn, token, now=t0 + 7 * 3600)               # used after 7 h: still fine
    assert auth.parent_for_token(conn, token, now=t0 + 7 * 3600 + 8 * 3600 + 1) is None


def test_forged_cookie_refused(app):
    c = TestClient(app)
    c.cookies.set(auth.COOKIE, "made-up-token")
    assert c.get("/api/overview").status_code == 401


def test_approval_records_the_parent_who_decided(app):
    c = TestClient(app)
    login(c, "dad", "demo")
    c.post("/api/consent", json={"told_child": True})
    pending = c.get("/api/approvals", params={"status": "pending"}).json()["items"]
    assert pending
    r = c.post(f"/api/approvals/{pending[0]['id']}/approve", json={"minutes": 30})
    assert r.status_code == 200                                  # no deadlock between the two locks
    who = app.state.runtime.conn.execute(
        "SELECT p.display_name FROM approval_requests a JOIN parents p ON p.id = a.decided_by WHERE a.id = ?",
        (pending[0]["id"],)).fetchone()[0]
    assert who == "Dad"
