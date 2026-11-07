from datetime import datetime
from types import SimpleNamespace

import pytest

from homenet import alerts, db, demo
from homenet.engine import Decision


@pytest.fixture(scope="module")
def day():
    conn = db.connect(":memory:")
    demo.run_day(conn)
    return conn


def rows(conn, kind, like=None):
    sql = "SELECT a.*, d.display_name AS dev FROM alerts a JOIN devices d ON d.id = a.device_id WHERE a.kind = ?"
    args = [kind]
    if like:
        sql += " AND message LIKE ?"
        args.append(f"%{like}%")
    return conn.execute(sql + " ORDER BY ts", args).fetchall()


# --- the simulated Thursday --------------------------------------------------------------------

def test_one_new_device_alert(day):
    r = rows(day, "new_device")
    assert len(r) == 1
    assert r[0]["dev"] == "Galaxy-A14"
    assert r[0]["ts"] == "2026-11-05T16:20:00"
    assert r[0]["severity"] == "warning"


def test_family_devices_raise_no_new_device_alert(day):
    known = {x["id"] for x in day.execute("SELECT id FROM devices WHERE known = 1")}
    assert known
    assert not {r["device_id"] for r in rows(day, "new_device")} & known


def test_two_approval_alerts(day):
    assert [r["ts"] for r in rows(day, "approval_waiting")] == ["2026-11-05T17:04:12", "2026-11-05T17:41:00"]


def test_one_explicit_alert_without_domain(day):
    r = rows(day, "explicit_blocked")
    assert len(r) == 1
    assert r[0]["ts"] == "2026-11-05T21:14:05"
    assert r[0]["severity"] == "critical"
    assert "redtube" not in r[0]["message"].lower()
    assert r[0]["message"] == "Explicit site blocked on Ana's phone."


def test_night_use_only_ana_phone(day):
    r = rows(day, "night_use")
    assert len(r) == 1
    assert r[0]["dev"] == "Ana's phone"
    assert r[0]["ts"] == "2026-11-05T23:06:00"
    assert r[0]["message"].startswith("Ana's phone was used at 23:06, during the night.")


def test_dns_bypass_alerts_for_ana_laptop(day):
    enc = rows(day, "dns_bypass", "encrypted DNS server")
    gone = rows(day, "dns_bypass", "may be bypassing")
    assert [(r["dev"], r["ts"]) for r in enc] == [("Ana's laptop", "2026-11-05T19:29:50")]
    assert len(gone) == 1 and gone[0]["dev"] == "Ana's laptop"
    assert gone[0]["severity"] == "critical"
    assert "2026-11-05T19:39:58" <= gone[0]["ts"] <= "2026-11-05T19:45:00"
    assert len(rows(day, "dns_bypass")) == 2


def test_check_bypass_is_idempotent(day):
    before = day.execute("SELECT COUNT(*) FROM alerts").fetchone()[0]
    alerts.check_bypass(day, datetime(2026, 11, 5, 19, 50))
    alerts.check_bypass(day, datetime(2026, 11, 5, 19, 50))
    assert day.execute("SELECT COUNT(*) FROM alerts").fetchone()[0] == before


# --- unit tests on a hand-made db ---------------------------------------------------------------

@pytest.fixture
def conn():
    return db.connect(":memory:")


def mk_device(c, name="Kid's phone", child=False, known=1):
    cid = None
    if child:
        cid = c.execute("INSERT INTO children(name, age, age_profile) VALUES ('Kid', 12, 13)").lastrowid
    did = c.execute("INSERT INTO devices(mac, display_name, child_id, known, first_seen, last_seen) "
                    "VALUES (?,?,?,?,?,?)",
                    (f"aa:{name}", name, cid, known, "2026-11-05T00:00:00", "2026-11-05T00:00:00")).lastrowid
    c.commit()
    return c.execute("SELECT * FROM devices WHERE id = ?", (did,)).fetchone()


def ev(ts, domain="x.com", source="dns"):
    return SimpleNamespace(ts=datetime.fromisoformat(ts), mac="m", domain=domain, source=source, bytes=0)


def dec(rule="default", decision="allowed", category="other"):
    return Decision(decision, "r", category, rule, None)


def store(c, device, e):
    c.execute("INSERT INTO queries(ts, device_id, domain, source, bytes, category, decision, reason) "
              "VALUES (?,?,?,?,0,'other','allowed','r')",
              (e.ts.isoformat(), device["id"], e.domain, e.source))
    c.commit()


def count(c, kind):
    return c.execute("SELECT COUNT(*) FROM alerts WHERE kind = ?", (kind,)).fetchone()[0]


def test_explicit_dedupe_window(conn):
    d = mk_device(conn)
    for t in ("2026-11-05T10:00:00", "2026-11-05T10:10:00"):
        alerts.on_query(conn, d, ev(t), dec("explicit", "blocked"))
    assert count(conn, "explicit_blocked") == 1
    alerts.on_query(conn, d, ev("2026-11-05T10:50:00"), dec("explicit", "blocked"))
    assert count(conn, "explicit_blocked") == 2


def test_new_device_only_unknown_and_once(conn):
    known = mk_device(conn, "A", known=1)
    unknown = mk_device(conn, "B", known=0)
    alerts.on_new_device(conn, known["id"], datetime(2026, 11, 5, 9))
    alerts.on_new_device(conn, unknown["id"], datetime(2026, 11, 5, 9))
    alerts.on_new_device(conn, unknown["id"], datetime(2026, 11, 5, 9, 5))
    assert count(conn, "new_device") == 1


def test_approval_one_per_request(conn):
    d = mk_device(conn)
    alerts.on_approval_request(conn, 1, d["id"], "shop.com", datetime(2026, 11, 5, 9))
    alerts.on_approval_request(conn, 1, d["id"], "shop.com", datetime(2026, 11, 5, 9))
    alerts.on_approval_request(conn, 2, d["id"], "shop.com", datetime(2026, 11, 5, 9, 30))
    assert count(conn, "approval_waiting") == 2


def test_night_window_crosses_midnight_once_per_night(conn):
    kid = mk_device(conn, child=True)
    adult = mk_device(conn, "Dad's phone")
    for t in ("2026-11-05T22:59:00", "2026-11-05T23:00:00", "2026-11-05T23:30:00", "2026-11-06T01:00:00"):
        alerts.on_query(conn, kid, ev(t), dec())
    assert count(conn, "night_use") == 1
    alerts.on_query(conn, kid, ev("2026-11-06T06:00:00"), dec())    # morning: not night
    assert count(conn, "night_use") == 1
    alerts.on_query(conn, kid, ev("2026-11-06T23:10:00"), dec())    # next night
    assert count(conn, "night_use") == 2
    alerts.on_query(conn, adult, ev("2026-11-07T23:10:00"), dec())
    assert count(conn, "night_use") == 2


def test_after_midnight_alone_belongs_to_previous_night(conn):
    kid = mk_device(conn, child=True)
    alerts.on_query(conn, kid, ev("2026-11-05T23:30:00"), dec())
    alerts.on_query(conn, kid, ev("2026-11-06T02:00:00"), dec())
    assert count(conn, "night_use") == 1


def test_night_ignores_system_and_marks_blocked(conn):
    kid = mk_device(conn, child=True)
    alerts.on_query(conn, kid, ev("2026-11-05T23:30:00"), dec("system", category="system"))
    assert count(conn, "night_use") == 0
    alerts.on_query(conn, kid, ev("2026-11-05T23:31:00"), dec("schedule", "blocked"))
    m = conn.execute("SELECT message FROM alerts WHERE kind='night_use'").fetchone()[0]
    assert m == "Kid's phone was used at 23:31, during the night. (blocked by schedule)"


def test_encrypted_dns_once_per_day(conn):
    d = mk_device(conn)
    for t in ("2026-11-05T10:00:00", "2026-11-05T15:00:00"):
        alerts.on_query(conn, d, ev(t, "dns.google"), dec("encrypted_dns", "blocked", "encrypted_dns"))
    assert count(conn, "dns_bypass") == 1
    alerts.on_query(conn, d, ev("2026-11-06T10:00:00", "dns.google"),
                    dec("encrypted_dns", "blocked", "encrypted_dns"))
    assert count(conn, "dns_bypass") == 2


def test_vanished_lookups_threshold_and_dedupe(conn):
    d = mk_device(conn)
    store(conn, d, ev("2026-11-05T10:00:00"))
    e1 = ev("2026-11-05T10:05:00", source="sni")
    store(conn, d, e1)
    alerts.on_query(conn, d, e1, dec())
    assert count(conn, "dns_bypass") == 0                      # only 5 minutes
    e2 = ev("2026-11-05T10:12:00", source="sni")
    store(conn, d, e2)
    alerts.on_query(conn, d, e2, dec())
    alerts.on_query(conn, d, e2, dec())
    assert count(conn, "dns_bypass") == 1


def test_vanished_without_any_dns_and_check_bypass(conn):
    d = mk_device(conn)
    store(conn, d, ev("2026-11-05T10:00:00", source="sni"))
    alerts.check_bypass(conn, datetime(2026, 11, 5, 10, 3))
    alerts.check_bypass(conn, datetime(2026, 11, 5, 10, 4))
    assert count(conn, "dns_bypass") == 1


def test_list_and_acknowledge(conn):
    d = mk_device(conn)
    alerts.on_query(conn, d, ev("2026-11-05T10:00:00"), dec("explicit", "blocked"))
    alerts.on_query(conn, d, ev("2026-11-05T12:00:00"), dec("explicit", "blocked"))
    allr = alerts.list_alerts(conn)
    assert [r["ts"] for r in allr] == ["2026-11-05T12:00:00", "2026-11-05T10:00:00"]
    assert len(alerts.list_alerts(conn, since="2026-11-05T11:00:00")) == 1
    alerts.acknowledge(conn, allr[0]["id"])
    open_ = alerts.list_alerts(conn, unacknowledged_only=True)
    assert [r["id"] for r in open_] == [allr[1]["id"]]
