import re
from datetime import datetime

import pytest
from fastapi import Depends
from fastapi.testclient import TestClient

from homenet import auth, consent
from homenet.app import create_app

NOW = datetime(2026, 11, 5, 22, 0)


@pytest.fixture()
def app():
    auth.reset_failures()
    a = create_app(":memory:", clock=lambda: NOW, background=False)
    a.state.runtime.start()
    a.state.runtime.tick()
    a.include_router(consent.router)

    @a.get("/api/test-guarded", dependencies=[Depends(consent.require_consent)])
    def guarded():
        return {"ok": True}

    yield a
    auth.reset_failures()


@pytest.fixture()
def client(app):
    c = TestClient(app)
    assert c.post("/api/auth/login", json={"username": "demo", "password": "demo"}).status_code == 200
    return c


def test_get_unconfirmed_with_one_notice_per_child(client):
    d = client.get("/api/consent").json()
    assert d["confirmed"] is False and d["confirmed_by"] is None and d["confirmed_at"] is None
    names = sorted(n["child_name"] for n in d["notice"])
    assert names == ["Ana", "Luka"]
    for n in d["notice"]:
        assert n["child_name"] in n["text"]
        assert "30 days" in n["text"]
        assert "{" not in n["text"] and "}" not in n["text"]
    assert len(d["does_not_see"]) >= 7


def test_post_requires_literal_true(client):
    assert client.post("/api/consent", json={"told_child": False}).status_code == 422
    assert client.post("/api/consent", json={}).status_code == 422
    assert client.post("/api/consent", json={"told_child": "yes"}).status_code == 422
    assert client.post("/api/consent", json={"told_child": True, "x": 1}).status_code == 422
    assert client.get("/api/consent").json()["confirmed"] is False


def test_confirm_and_withdraw(client):
    d = client.post("/api/consent", json={"told_child": True}).json()
    assert d["confirmed"] is True and d["confirmed_by"] == "Mom" and d["confirmed_at"]
    assert client.get("/api/consent").json()["confirmed"] is True
    d = client.post("/api/consent/withdraw").json()
    assert d["confirmed"] is False and d["confirmed_by"] is None


def test_require_consent_dependency(client):
    r = client.get("/api/test-guarded")
    assert r.status_code == 403
    assert r.json()["detail"]["code"] == "consent_required"
    client.post("/api/consent", json={"told_child": True})
    assert client.get("/api/test-guarded").status_code == 200
    client.post("/api/consent/withdraw")
    assert client.get("/api/test-guarded").status_code == 403


def test_does_not_see_route(client):
    items = client.get("/api/consent/does-not-see").json()
    assert all(i["title"] and i["text"] for i in items)


def test_all_consent_routes_need_login(app):
    c = TestClient(app)
    assert c.get("/api/consent").status_code == 401
    assert c.post("/api/consent", json={"told_child": True}).status_code == 401
    assert c.post("/api/consent/withdraw").status_code == 401
    assert c.get("/api/consent/does-not-see").status_code == 401


def test_notice_never_claims_to_read_messages(client):
    for n in client.get("/api/consent").json()["notice"]:
        text = n["text"]
        assert "does NOT" in text or "does not" in text
        sentences = re.split(r"(?<=[.!?])\s+", text)
        for s in sentences:
            if "messages" in s:
                assert "not" in s.lower()
