import sqlite3

import pytest

from homenet import db

TS = "2026-11-07T10:00:00"


@pytest.fixture
def conn():
    c = db.connect(":memory:")
    yield c
    c.close()


def test_all_tables_exist(conn):
    names = {r["name"] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert set(db.TABLES) <= names


def test_one_row_per_table_round_trip(conn):
    conn.execute("INSERT INTO parents(username, display_name, password_hash, created_at) VALUES ('mom','Mom','x',?)", (TS,))
    conn.execute("INSERT INTO children(name, age, age_profile) VALUES ('Ana', 14, 13)")
    conn.execute(
        "INSERT INTO devices(mac, hostname, display_name, kind, child_id, first_seen, last_seen) "
        "VALUES ('aa:bb:cc:dd:ee:01','ana-phone','Ana phone','phone',1,?,?)", (TS, TS))
    conn.execute(
        "INSERT INTO queries(ts, device_id, domain, source, bytes, category, decision, reason) "
        "VALUES (?,1,'youtube.com','dns',0,'video','allowed','no rule')", (TS,))
    conn.execute("INSERT INTO rules(child_id, category, action) VALUES (1,'games','block')")
    conn.execute("INSERT INTO schedules(child_id, name, days, start, end) VALUES (1,'School nights','sun,mon,tue,wed,thu','22:00','07:00')")
    conn.execute("INSERT INTO pauses(child_id, started_at, until_ts) VALUES (1,?,?)", (TS, "2026-11-07T11:00:00"))
    conn.execute("INSERT INTO approval_requests(ts, device_id, domain, status) VALUES (?,1,'play.google.com','pending')", (TS,))
    conn.execute("INSERT INTO alerts(ts, kind, severity, device_id, message) VALUES (?,'new_device','warning',1,'New device')", (TS,))
    conn.commit()

    assert conn.execute("SELECT username FROM parents").fetchone()["username"] == "mom"
    assert conn.execute("SELECT age_profile FROM children").fetchone()["age_profile"] == 13
    assert conn.execute("SELECT child_id FROM devices").fetchone()["child_id"] == 1
    assert conn.execute("SELECT decision FROM queries").fetchone()["decision"] == "allowed"
    assert conn.execute("SELECT action FROM rules").fetchone()["action"] == "block"
    assert conn.execute("SELECT start FROM schedules").fetchone()["start"] == "22:00"
    assert conn.execute("SELECT until_ts FROM pauses").fetchone()["until_ts"].endswith("11:00:00")
    assert conn.execute("SELECT status FROM approval_requests").fetchone()["status"] == "pending"
    assert conn.execute("SELECT kind FROM alerts").fetchone()["kind"] == "new_device"
    assert db.get_setting(conn, "retention_days") == "30"


def test_settings_set_and_defaults(conn):
    db.set_setting(conn, "retention_days", "14")
    assert db.get_setting(conn, "retention_days") == "14"
    assert db.get_setting(conn, "consent_confirmed") == "0"


def test_bad_values_are_refused(conn):
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO children(name, age, age_profile) VALUES ('X', 10, 10)")
    conn.execute("INSERT INTO devices(mac, display_name, first_seen, last_seen) VALUES ('m','d',?,?)", (TS, TS))
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO queries(ts, device_id, domain, source, category, decision, reason) VALUES (?,1,'a','dns','x','maybe','r')", (TS,))


def test_deleting_device_removes_its_queries(conn):
    conn.execute("INSERT INTO devices(mac, display_name, first_seen, last_seen) VALUES ('m','d',?,?)", (TS, TS))
    conn.execute("INSERT INTO queries(ts, device_id, domain, source, category, decision, reason) VALUES (?,1,'a','dns','x','allowed','r')", (TS,))
    conn.execute("DELETE FROM devices WHERE id = 1")
    assert conn.execute("SELECT COUNT(*) FROM queries").fetchone()[0] == 0
