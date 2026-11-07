import pytest

from homenet import db
from homenet.timeuse import ESTIMATE_NOTE, estimate, estimate_for_child, estimate_for_device


def row(ts, domain="www.youtube.com", cat="video", dev=1, decision="allowed"):
    return {"ts": f"2026-11-07T{ts}", "device_id": dev, "domain": domain,
            "category": cat, "decision": decision}


def test_three_lookups_make_five_minutes():
    r = estimate([row("10:00:00"), row("10:02:00"), row("10:04:00")])
    assert r.total_minutes == 5.0
    assert r.by_category == {"video": 5.0}
    assert r.sessions == 1
    assert r.note == ESTIMATE_NOTE


def test_gap_splits_sessions():
    r = estimate([row("10:00:00"), row("10:06:00")])
    assert r.sessions == 2
    assert r.total_minutes == 2.0


def test_gap_exactly_threshold_joins():
    r = estimate([row("10:00:00"), row("10:05:00")])
    assert r.sessions == 1
    assert r.total_minutes == 6.0


def test_ignored_rows():
    r = estimate([
        row("10:00:00", decision="blocked"),
        row("10:01:00", cat="system", domain="time.windows.com"),
        row("10:02:00", cat="encrypted_dns", domain="dns.google"),
    ])
    assert r.total_minutes == 0.0
    assert r.sessions == 0


def test_devices_separate():
    r = estimate([row("10:00:00", dev=1), row("10:02:00", dev=2)])
    assert r.total_minutes == 2.0
    assert r.sessions == 2


def test_site_folding_and_ordering():
    r = estimate([row("10:00:00", "i.ytimg.com"), row("10:01:00", "www.youtube.com"),
                  row("10:30:00", "example.org", "other")])
    assert r.by_site["youtube.com"] == 2.0
    assert "ytimg.com" not in r.by_site
    assert list(r.by_site)[0] == "youtube.com"


def test_by_hour_sums_to_total():
    r = estimate([row("09:58:00"), row("09:59:00"), row("14:00:00"), row("14:03:30")])
    assert len(r.by_hour) == 24
    assert sum(r.by_hour) == pytest.approx(r.total_minutes, abs=0.2)
    assert r.by_hour[9] > 0 and r.by_hour[14] > 0


def _setup():
    conn = db.connect(":memory:")
    conn.execute("INSERT INTO children(id,name,age,age_profile) VALUES (1,'A',10,8),(2,'B',15,16)")
    for i, (mac, child) in enumerate([("aa", 1), ("bb", 1), ("cc", 2)], start=1):
        conn.execute(
            "INSERT INTO devices(id,mac,display_name,child_id,first_seen,last_seen) "
            "VALUES (?,?,?,?,'x','x')", (i, mac, mac, child))

    def q(ts, dev):
        conn.execute(
            "INSERT INTO queries(ts,device_id,domain,source,category,decision,reason) "
            "VALUES (?,?,'youtube.com','dns','video','allowed','ok')", (ts, dev))

    q("2026-11-07T10:00:00", 1)
    q("2026-11-07T10:02:00", 1)   # device 1: 2 + 1 = 3
    q("2026-11-07T11:00:00", 2)   # device 2: 1
    q("2026-11-07T10:00:00", 3)   # other child
    q("2026-11-08T10:00:00", 1)   # outside range
    q("2026-11-06T23:59:00", 1)   # outside range
    conn.commit()
    return conn


def test_estimate_for_child():
    conn = _setup()
    r = estimate_for_child(conn, 1, "2026-11-07T00:00:00", "2026-11-08T00:00:00")
    assert r.total_minutes == 4.0
    assert r.sessions == 2
    r2 = estimate_for_child(conn, 2, "2026-11-07T00:00:00", "2026-11-08T00:00:00")
    assert r2.total_minutes == 1.0


def test_estimate_for_device():
    conn = _setup()
    r = estimate_for_device(conn, 1, "2026-11-07T00:00:00", "2026-11-08T00:00:00")
    assert r.total_minutes == 3.0
