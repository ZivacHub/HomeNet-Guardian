from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from homenet import engine
from homenet.app import create_app

NOW = datetime(2026, 11, 5, 22, 0)


@pytest.fixture()
def app():
    a = create_app(":memory:", clock=lambda: NOW, background=False)
    a.state.runtime.start()
    a.state.runtime.tick()
    return a


def login(c, username="demo", password="demo"):
    r = c.post("/api/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    return c


@pytest.fixture()
def client(app):
    return login(TestClient(app))


def _by_name(client, path, name):
    return next(i for i in client.get(path).json()["items"] if i["name"] == name)


def _device(client, name):
    return next(d for d in client.get("/api/devices").json()["items"] if d["display_name"] == name)


def test_health_is_public(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "name": "HomeNet Guardian"}


def test_overview(client):
    j = client.get("/api/overview").json()
    assert j["now"] == "2026-11-05T22:00:00"
    assert {c["name"] for c in j["children"]} == {"Ana", "Luka"}
    luka = next(c for c in j["children"] if c["name"] == "Luka")
    assert luka["lookups"] > 0 and luka["blocked"] > 0
    assert len(luka["top_categories"]) <= 3
    assert j["pending_approvals"] == 1
    assert j["unacknowledged_alerts"] >= 1 and len(j["newest_alerts"]) <= 10
    assert isinstance(j["online_devices"], list)


def test_devices_and_patch(client):
    items = client.get("/api/devices").json()["items"]
    assert any(d["child_name"] == "Luka" for d in items)
    assert all("online" in d and "lookups_today" in d for d in items)
    dev = _device(client, "Luka's iPad")
    r = client.patch(f"/api/devices/{dev['id']}", json={"display_name": "Luka tablet", "known": True})
    assert r.status_code == 200 and r.json()["display_name"] == "Luka tablet"
    r = client.patch(f"/api/devices/{dev['id']}", json={"child_id": None})
    assert r.json()["child_id"] is None and r.json()["display_name"] == "Luka tablet"


def test_device_errors(client):
    assert client.patch("/api/devices/9999", json={"known": True}).status_code == 404
    dev = _device(client, "Luka's iPad")
    assert client.patch(f"/api/devices/{dev['id']}", json={"child_id": 9999}).status_code == 404
    assert client.patch(f"/api/devices/{dev['id']}", json={"display_name": ""}).status_code == 422


def test_assigning_visitor_phone_changes_decisions(app, client):
    phone = _device(client, "Galaxy-A14")
    luka = _by_name(client, "/api/children", "Luka")
    rt = app.state.runtime
    row = rt.conn.execute("SELECT * FROM devices WHERE id = ?", (phone["id"],)).fetchone()
    at = datetime(2026, 11, 5, 15, 0)
    assert engine.Engine(rt.conn).decide(row, "instagram.com", at).decision == "allowed"
    assert client.patch(f"/api/devices/{phone['id']}", json={"child_id": luka["id"]}).status_code == 200
    row = rt.conn.execute("SELECT * FROM devices WHERE id = ?", (phone["id"],)).fetchone()
    assert engine.Engine(rt.conn).decide(row, "instagram.com", at).decision == "blocked"


def test_children(client):
    items = client.get("/api/children").json()["items"]
    luka = next(c for c in items if c["name"] == "Luka")
    assert luka["age_profile"] == 8 and luka["profile_label"] == "Up to 9"
    r = client.patch(f"/api/children/{luka['id']}", json={"age_profile": 13})
    assert r.json()["age_profile"] == 13 and r.json()["name"] == "Luka"
    assert client.patch(f"/api/children/{luka['id']}", json={"age_profile": 10}).status_code == 422
    assert client.patch("/api/children/9999", json={"age_profile": 8}).status_code == 404


def test_activity_filters_and_paging(client):
    j = client.get("/api/activity").json()
    assert len(j["items"]) == 100 and j["next_before_id"] is not None
    assert all(i["ts"] <= "2026-11-05T22:00:00" for i in j["items"])
    ids = [i["id"] for i in j["items"]]
    assert ids == sorted(ids, reverse=True) and "device_name" in j["items"][0]

    blocked = client.get("/api/activity?decision=blocked&limit=500").json()["items"]
    assert blocked and all(i["decision"] == "blocked" for i in blocked)

    dev = _device(client, "Luka's iPad")
    mine = client.get(f"/api/activity?device_id={dev['id']}&limit=500").json()["items"]
    assert mine and all(i["device_id"] == dev["id"] for i in mine)

    page1 = client.get("/api/activity?limit=5").json()
    page2 = client.get(f"/api/activity?limit=5&before_id={page1['next_before_id']}").json()
    assert len(page1["items"]) == 5 and len(page2["items"]) == 5
    assert max(i["id"] for i in page2["items"]) < min(i["id"] for i in page1["items"])

    one = client.get("/api/activity?q=youtube&limit=500").json()["items"]
    assert one and all("youtube" in i["domain"] for i in one)
    assert client.get("/api/activity?limit=0").status_code == 422
    assert client.get("/api/activity?decision=maybe").status_code == 422


def test_timeuse(client):
    luka = _by_name(client, "/api/children", "Luka")
    j = client.get(f"/api/timeuse?child_id={luka['id']}").json()
    assert j["total_minutes"] > 0 and "estimate" in j["note"].lower() and len(j["by_hour"]) == 24
    assert client.get(f"/api/timeuse?child_id={luka['id']}&date=2026-11-04").json()["total_minutes"] == 0
    assert client.get("/api/timeuse").status_code == 422
    assert client.get("/api/timeuse?child_id=9999").status_code == 404
    assert client.get(f"/api/timeuse?child_id={luka['id']}&date=nope").status_code == 422


def test_rules(client):
    j = client.get("/api/rules").json()
    fixed = {c["name"] for c in j["categories"] if c["fixed"]}
    assert fixed == {"explicit", "encrypted_dns"}
    ana = _by_name(client, "/api/children", "Ana")
    r = client.put("/api/rules", json={"child_id": ana["id"], "category": "games", "action": "block"})
    assert r.status_code == 200
    rules = client.get("/api/rules").json()["rules"]
    assert {"child_id": ana["id"], "category": "games", "action": "block"} in rules
    client.put("/api/rules", json={"child_id": ana["id"], "category": "games", "action": None})
    assert {"child_id": ana["id"], "category": "games", "action": "block"} not in client.get("/api/rules").json()["rules"]
    assert client.put("/api/rules", json={"child_id": None, "category": "explicit", "action": "allow"}).status_code == 422
    assert client.put("/api/rules", json={"child_id": None, "category": "nope", "action": "block"}).status_code == 422
    assert client.put("/api/rules", json={"child_id": None, "category": "games", "action": "stop"}).status_code == 422


def test_schedules(client):
    ana = _by_name(client, "/api/children", "Ana")
    n = len(client.get("/api/schedules").json()["items"])
    r = client.post("/api/schedules", json={"child_id": ana["id"], "name": "Homework", "days": "Tue, mon",
                                            "start": "16:00", "end": "18:00"})
    assert r.status_code == 201 and r.json()["days"] == "mon,tue"
    sid = r.json()["id"]
    assert len(client.get("/api/schedules").json()["items"]) == n + 1
    r = client.patch(f"/api/schedules/{sid}", json={"enabled": False, "end": "18:30"})
    assert r.json()["enabled"] is False and r.json()["end"] == "18:30" and r.json()["start"] == "16:00"
    assert client.delete(f"/api/schedules/{sid}").status_code == 200
    assert client.delete(f"/api/schedules/{sid}").status_code == 404
    assert client.patch("/api/schedules/9999", json={"enabled": True}).status_code == 404


@pytest.mark.parametrize("patch", [{"start": "25:00"}, {"start": "7:00"}, {"end": "noon"}, {"days": "funday"}, {"days": ""}])
def test_schedule_bad_input(client, patch):
    ana = _by_name(client, "/api/children", "Ana")
    body = {"child_id": ana["id"], "name": "x", "days": "mon", "start": "10:00", "end": "11:00", **patch}
    assert client.post("/api/schedules", json=body).status_code == 422
    sid = client.get("/api/schedules").json()["items"][0]["id"]
    assert client.patch(f"/api/schedules/{sid}", json=patch).status_code == 422


def test_schedule_unknown_child(client):
    body = {"child_id": 9999, "name": "x", "days": "mon", "start": "10:00", "end": "11:00"}
    assert client.post("/api/schedules", json=body).status_code == 404


def test_pause_and_resume(client):
    luka = _by_name(client, "/api/children", "Luka")
    assert client.get("/api/pauses").json()["items"] == []
    r = client.post("/api/pause", json={"child_id": luka["id"], "minutes": 30})
    assert r.status_code == 201 and r.json()["until_ts"] == "2026-11-05T22:30:00"
    items = client.get("/api/pauses").json()["items"]
    assert len(items) == 1 and items[0]["child_name"] == "Luka"
    assert client.post("/api/resume", json={"child_id": luka["id"]}).status_code == 200
    assert client.get("/api/pauses").json()["items"] == []
    assert client.post("/api/pause", json={"child_id": None, "minutes": 0}).status_code == 422
    assert client.post("/api/pause", json={"child_id": None, "minutes": 1441}).status_code == 422
    assert client.post("/api/pause", json={"child_id": 9999, "minutes": 5}).status_code == 404
    assert client.post("/api/pause", json={"child_id": None, "minutes": 5}).status_code == 201


def test_approval_flow(client):
    j = client.get("/api/approvals?status=pending").json()
    assert "Ask to Buy" in j["note"]
    assert len(j["items"]) == 1
    req = j["items"][0]
    assert req["device_name"] == "Luka's iPad" and req["ts"].startswith("2026-11-05T17:04")
    r = client.post(f"/api/approvals/{req['id']}/approve", json={"minutes": 15})
    assert r.status_code == 200 and r.json()["status"] == "approved"
    assert r.json()["approved_until"] == "2026-11-05T22:15:00"
    assert client.post(f"/api/approvals/{req['id']}/approve").status_code == 409
    assert client.post(f"/api/approvals/{req['id']}/deny").status_code == 409
    assert client.post("/api/approvals/9999/approve").status_code == 404
    assert client.post(f"/api/approvals/{req['id']}/approve", json={"minutes": 0}).status_code == 422
    assert client.get("/api/approvals?status=pending").json()["items"] == []
    assert client.get("/api/approvals?status=bogus").status_code == 422


def test_deny(client):
    req = client.get("/api/approvals?status=pending").json()["items"][0]
    r = client.post(f"/api/approvals/{req['id']}/deny")
    assert r.status_code == 200 and r.json()["status"] == "denied"


def test_alerts(client):
    items = client.get("/api/alerts").json()["items"]
    assert items
    unack = client.get("/api/alerts?unacknowledged=true").json()["items"]
    assert len(unack) == len(items)
    aid = items[0]["id"]
    assert client.post(f"/api/alerts/{aid}/ack").json()["acknowledged"] is True
    assert len(client.get("/api/alerts?unacknowledged=true").json()["items"]) == len(items) - 1
    assert [a["id"] for a in client.get("/api/alerts?unacknowledged=false").json()["items"]] == [aid]
    assert client.post("/api/alerts/99999/ack").status_code == 404


def test_settings(client):
    j = client.get("/api/settings").json()
    assert j["retention_days"] == 30 and j["approval_minutes_default"] == 30
    assert j["night_start"] == "23:00" and j["consent_confirmed"] is False
    r = client.patch("/api/settings", json={"retention_days": 90, "approval_minutes_default": 45})
    assert r.json()["retention_days"] == 90 and r.json()["approval_minutes_default"] == 45
    assert client.patch("/api/settings", json={"retention_days": 0}).status_code == 422
    assert client.patch("/api/settings", json={"approval_minutes_default": 1441}).status_code == 422
    assert client.patch("/api/settings", json={"night_start": "20:00"}).status_code == 422


def test_meta(client):
    j = client.get("/api/meta").json()
    assert j["simulated"] is True and j["today"] == "2026-11-05"
    assert "games" in [c["name"] for c in j["categories"]]
    assert {p["age_profile"] for p in j["age_profiles"]} == {8, 13, 16}
    assert j["payment_note"] and "estimate" in j["estimate_note"].lower()


def test_date_change():
    now = [datetime(2026, 11, 5, 23, 59, 50)]
    a = create_app(":memory:", clock=lambda: now[0], background=False)
    rt = a.state.runtime
    rt.start()
    rt.tick()
    c = login(TestClient(a))
    assert rt._processed_until() == datetime(2026, 11, 5, 23, 59, 50)
    now[0] = datetime(2026, 11, 6, 0, 0, 30)
    rt.tick()
    assert rt._processed_until() == datetime(2026, 11, 6, 0, 0, 30)
    q = lambda d: rt.conn.execute("SELECT COUNT(*) FROM queries WHERE ts LIKE ?", (d + "%",)).fetchone()[0]
    assert q("2026-11-05") > 0
    now[0] = datetime(2026, 11, 6, 8, 0)      # the simulated router is quiet until 06:30
    rt.tick()
    assert q("2026-11-06") > 0
    assert c.get("/api/meta").json()["today"] == "2026-11-06"


def test_catch_up_after_days_off():
    now = [datetime(2026, 11, 5, 12, 0)]
    a = create_app(":memory:", clock=lambda: now[0], background=False)
    rt = a.state.runtime
    rt.start()
    rt.tick()
    now[0] = datetime(2026, 11, 7, 9, 0)
    rt.tick()
    days = {r[0] for r in rt.conn.execute("SELECT DISTINCT substr(ts, 1, 10) FROM queries")}
    assert days == {"2026-11-05", "2026-11-06", "2026-11-07"}
    assert rt.tick() == 0       # nothing new until the clock moves


def test_start_does_not_reseed(app):
    rt = app.state.runtime
    n = rt.conn.execute("SELECT COUNT(*) FROM parents").fetchone()[0]
    rt.started = False
    rt.start()
    assert rt.conn.execute("SELECT COUNT(*) FROM parents").fetchone()[0] == n == 2


def test_lifespan_runs_with_context_manager():
    a = create_app(":memory:", clock=lambda: NOW, background=False)
    with TestClient(a) as c:
        assert login(c).get("/api/overview").status_code == 200
