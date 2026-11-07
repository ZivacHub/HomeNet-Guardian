from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from homenet import auth, db, retention
from homenet.app import create_app

NOW = datetime(2026, 12, 6, 12, 0)


def _seed(conn):
    t0 = "2026-11-01T00:00:00"
    conn.execute("INSERT INTO devices(mac, display_name, first_seen, last_seen) VALUES ('m','d',?,?)", (t0, t0))
    for age_days, status in [(31, "approved"), (31, "pending"), (29, "denied")]:
        ts = (NOW - timedelta(days=age_days)).isoformat()
        conn.execute("INSERT INTO queries(ts, device_id, domain, source, category, decision, reason) "
                     "VALUES (?,1,'a.com','dns','other','allowed','r')", (ts,))
        conn.execute("INSERT INTO alerts(ts, kind, severity, device_id, message) VALUES (?,'x','info',1,'m')", (ts,))
        conn.execute("INSERT INTO approval_requests(ts, device_id, domain, status) VALUES (?,1,'p.com',?)", (ts, status))
    conn.commit()


def count(conn, table):
    return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def test_records_older_than_30_days_are_removed():
    conn = db.connect(":memory:")
    _seed(conn)
    deleted = retention.cleanup(conn, NOW)
    assert deleted["queries"] == 2 and count(conn, "queries") == 1          # the 29-day-old one stays
    assert count(conn, "alerts") == 1
    # a 31-day-old request that still waits for a parent is kept; the answered one is removed
    assert [r[0] for r in conn.execute("SELECT status FROM approval_requests ORDER BY id")] == ["pending", "denied"]


def test_retention_setting_is_respected():
    conn = db.connect(":memory:")
    _seed(conn)
    db.set_setting(conn, "retention_days", "60")
    retention.cleanup(conn, NOW)
    assert count(conn, "queries") == 3


def test_runtime_cleans_up_on_the_simulation_clock():
    now = [datetime(2026, 11, 5, 12, 0)]
    a = create_app(":memory:", clock=lambda: now[0], background=False)
    rt = a.state.runtime
    rt.start()
    rt.tick()
    assert count(rt.conn, "queries") > 0
    now[0] = datetime(2026, 12, 7, 9, 0)        # 32 days later
    rt.tick()
    oldest = rt.conn.execute("SELECT MIN(ts) FROM queries").fetchone()[0]
    assert oldest >= "2026-11-07"


@pytest.fixture()
def client():
    auth.reset_failures()
    a = create_app(":memory:", clock=lambda: datetime(2026, 11, 5, 22, 0), background=False)
    a.state.runtime.start()
    a.state.runtime.tick()
    c = TestClient(a)
    assert c.post("/api/auth/login", json={"username": "demo", "password": "demo"}).status_code == 200
    c.rt = a.state.runtime
    return c


def test_delete_everything_needs_the_word_delete(client):
    before = client.get("/api/data/summary").json()["counts"]
    assert before["queries"] > 2000 and before["alerts"] > 0
    for word in ("delete", "yes", ""):
        assert client.post("/api/data/delete-all", json={"confirm": word}).status_code == 422
    assert client.get("/api/data/summary").json()["counts"] == before


def test_delete_everything_wipes_activity_keeps_accounts(client):
    r = client.post("/api/data/delete-all", json={"confirm": "DELETE"})
    assert r.status_code == 200
    assert r.json()["summary"]["counts"] == {"queries": 0, "alerts": 0, "approval_requests": 0, "pauses": 0}
    conn = client.rt.conn
    assert count(conn, "parents") == 2 and count(conn, "children") == 2 and count(conn, "devices") >= 8
    assert count(conn, "schedules") > 0
    assert client.get("/api/auth/me").status_code == 200          # still logged in


def test_data_routes_need_login():
    a = create_app(":memory:", background=False)
    c = TestClient(a)
    assert c.get("/api/data/summary").status_code == 401
    assert c.post("/api/data/delete-all", json={"confirm": "DELETE"}).status_code == 401
