from datetime import datetime, timedelta

import pytest

from homenet import db, engine
from homenet.adapters.base import NetEvent

# 2026-11-05 is a Thursday (a school night), 2026-11-06 a Friday, 2026-11-07 a Saturday
THU = datetime(2026, 11, 5)
FRI = datetime(2026, 11, 6)
SAT = datetime(2026, 11, 7)


def at(day, hh, mm=0):
    return day.replace(hour=hh, minute=mm)


@pytest.fixture
def home():
    conn = db.connect(":memory:")
    ana = engine.add_child(conn, "Ana", 14, 13)
    luka = engine.add_child(conn, "Luka", 9, 8)
    conn.execute("INSERT INTO parents(username, display_name, password_hash, created_at) "
                 "VALUES ('mom','Mom','x','2026-11-01T00:00:00')")
    t0 = "2026-11-01T00:00:00"
    for mac, name, child in [("aa:00:00:00:00:01", "Ana phone", ana),
                             ("aa:00:00:00:00:02", "Luka iPad", luka),
                             ("aa:00:00:00:00:03", "Dad phone", None)]:
        conn.execute("INSERT INTO devices(mac, hostname, display_name, child_id, known, first_seen, last_seen) "
                     "VALUES (?,?,?,?,1,?,?)", (mac, name, name, child, t0, t0))
    conn.commit()
    yield conn, engine.Engine(conn), {"ana": ana, "luka": luka}
    conn.close()


DEV = {"ana": "aa:00:00:00:00:01", "luka": "aa:00:00:00:00:02", "dad": "aa:00:00:00:00:03"}


def run(eng, who, domain, ts):
    return eng.process(NetEvent(ts, DEV[who], domain))


CASES = [
    # (who, domain, time, expected decision, rule that decided)
    ("ana", "redtube.com", at(THU, 15), "blocked", "explicit"),
    ("dad", "www.redtube.com", at(THU, 15), "blocked", "explicit"),          # adults too
    ("dad", "dns.google", at(THU, 15), "blocked", "encrypted_dns"),
    ("luka", "connectivitycheck.gstatic.com", at(THU, 22), "allowed", "system"),  # even at bedtime
    ("ana", "www.tiktok.com", at(THU, 15), "allowed", "default"),
    ("luka", "www.tiktok.com", at(THU, 15), "blocked", "category"),        # social blocked for age 8
    ("luka", "www.roblox.com", at(THU, 17), "allowed", "default"),
    ("luka", "www.youtube.com", at(THU, 20, 29), "allowed", "default"),
    ("luka", "www.youtube.com", at(THU, 20, 30), "blocked", "schedule"),   # bedtime 20:30
    ("luka", "www.youtube.com", at(FRI, 6, 59), "blocked", "schedule"),    # still bedtime next morning
    ("luka", "www.youtube.com", at(FRI, 7, 0), "allowed", "default"),
    ("ana", "www.instagram.com", at(THU, 21, 59), "allowed", "default"),
    ("ana", "www.instagram.com", at(THU, 22, 0), "blocked", "schedule"),   # school night 22:00
    ("ana", "www.instagram.com", at(FRI, 6, 29), "blocked", "schedule"),
    ("ana", "www.instagram.com", at(FRI, 22, 30), "allowed", "default"),   # Friday: weekend rule
    ("ana", "www.instagram.com", at(FRI, 23, 30), "blocked", "schedule"),  # weekend nights 23:30
    ("ana", "www.instagram.com", at(SAT, 6, 59), "blocked", "schedule"),
    ("dad", "www.instagram.com", at(THU, 23, 30), "allowed", "default"),   # schedules are for kids
    ("ana", "buy.itunes.apple.com", at(THU, 15), "blocked", "payment"),
    ("dad", "buy.itunes.apple.com", at(THU, 15), "allowed", "default"),    # adults buy freely
]


@pytest.mark.parametrize("who,domain,ts,expected,rule", CASES)
def test_rule_table(home, who, domain, ts, expected, rule):
    _, eng, _ = home
    d = run(eng, who, domain, ts)
    assert (d.decision, d.rule) == (expected, rule), d.reason


def test_every_decision_is_stored_with_reason(home):
    conn, eng, _ = home
    run(eng, "luka", "www.tiktok.com", at(THU, 15))
    row = conn.execute("SELECT * FROM queries").fetchone()
    assert (row["decision"], row["category"], row["reason"]) == ("blocked", "social", "Social blocked for Luka")


def test_category_rule_child_overrides_home(home):
    conn, eng, kids = home
    engine.set_category_rule(conn, None, "games", "block")
    assert run(eng, "ana", "www.roblox.com", at(THU, 15)).decision == "blocked"
    engine.set_category_rule(conn, kids["ana"], "games", "allow")
    assert run(eng, "ana", "www.roblox.com", at(THU, 15, 1)).decision == "allowed"
    assert run(eng, "dad", "www.roblox.com", at(THU, 15, 1)).reason == "Games blocked for the whole home"
    engine.set_category_rule(conn, None, "games", None)
    assert run(eng, "dad", "www.roblox.com", at(THU, 15, 2)).decision == "allowed"


def test_explicit_cannot_be_unblocked(home):
    conn, _, kids = home
    with pytest.raises(ValueError):
        engine.set_category_rule(conn, kids["ana"], "explicit", "allow")


def test_pause_child_then_resume(home):
    conn, eng, kids = home
    engine.pause(conn, kids["ana"], at(THU, 16), 60)
    d = run(eng, "ana", "www.wikipedia.org", at(THU, 16, 30))
    assert (d.decision, d.reason) == ("blocked", "Internet paused (Ana) until 17:00")
    assert run(eng, "luka", "www.roblox.com", at(THU, 16, 30)).decision == "allowed"
    engine.resume(conn, kids["ana"], at(THU, 16, 40))
    assert run(eng, "ana", "www.wikipedia.org", at(THU, 16, 41)).decision == "allowed"


def test_pause_whole_home(home):
    conn, eng, _ = home
    engine.pause(conn, None, at(THU, 18), 30)
    assert run(eng, "dad", "www.youtube.com", at(THU, 18, 10)).rule == "pause"
    assert run(eng, "dad", "www.youtube.com", at(THU, 18, 30)).decision == "allowed"


# --- payments (step 1.5) ---------------------------------------------------------------------

def test_payment_attempt_approve_30_minutes_then_blocked_again(home):
    conn, eng, _ = home
    t = at(THU, 17, 4)
    d1 = run(eng, "luka", "buy.itunes.apple.com", t)
    assert (d1.decision, d1.rule) == ("blocked", "payment") and d1.request_id
    # retry before the parent answers: same request, not a second one
    d2 = run(eng, "luka", "apps.apple.com", t + timedelta(minutes=2))
    assert d2.request_id == d1.request_id
    assert conn.execute("SELECT COUNT(*) FROM approval_requests").fetchone()[0] == 1

    engine.approve(conn, d1.request_id, 1, at(THU, 17, 8), 30)
    ok = run(eng, "luka", "buy.itunes.apple.com", at(THU, 17, 12))
    assert (ok.decision, ok.reason) == ("allowed", "Approved by Mom until 17:38")
    assert run(eng, "luka", "apps.apple.com", at(THU, 17, 37)).decision == "allowed"   # minute 29
    late = run(eng, "luka", "buy.itunes.apple.com", at(THU, 17, 39))                   # minute 31
    assert (late.decision, late.rule) == ("blocked", "payment")
    assert late.request_id != d1.request_id                                            # new request

    # the approval does not carry over to another child's device
    assert run(eng, "ana", "buy.itunes.apple.com", at(THU, 17, 15)).decision == "blocked"


def test_deny_and_decision_log(home):
    conn, eng, _ = home
    d = run(eng, "luka", "pay.google.com", at(THU, 17))
    engine.deny(conn, d.request_id, 1, at(THU, 17, 1))
    assert run(eng, "luka", "pay.google.com", at(THU, 17, 2)).decision == "blocked"
    rows = conn.execute("SELECT status, decided_by FROM approval_requests ORDER BY id").fetchall()
    assert [tuple(r) for r in rows] == [("denied", 1), ("pending", None)]
    with pytest.raises(ValueError):
        engine.deny(conn, d.request_id, 1, at(THU, 17, 3))          # already decided


def test_expire_marks_old_approvals(home):
    conn, eng, _ = home
    d = run(eng, "luka", "pay.google.com", at(THU, 17))
    engine.approve(conn, d.request_id, 1, at(THU, 17, 1), 30)
    assert engine.expire_approvals(conn, at(THU, 17, 20)) == 0
    assert engine.expire_approvals(conn, at(THU, 17, 31)) == 1


def test_approve_bounds(home):
    conn, eng, _ = home
    d = run(eng, "luka", "pay.google.com", at(THU, 17))
    with pytest.raises(ValueError):
        engine.approve(conn, d.request_id, 1, at(THU, 17, 1), 0)


# --- devices ---------------------------------------------------------------------------------

def test_random_mac_recognised_by_hostname(home):
    conn, eng, _ = home
    eng.process(NetEvent(at(THU, 15), "da:11:22:33:44:55", "www.tiktok.com"), hostname="Luka iPad")
    assert conn.execute("SELECT COUNT(*) FROM devices").fetchone()[0] == 3
    assert conn.execute("SELECT mac FROM devices WHERE hostname='Luka iPad'").fetchone()[0] == "da:11:22:33:44:55"


def test_unknown_device_registered_unknown(home):
    conn, eng, _ = home
    eng.process(NetEvent(at(THU, 16, 20), "da:4f:91:3e:7c:09", "www.youtube.com"), hostname="Galaxy-A14")
    row = conn.execute("SELECT * FROM devices WHERE hostname='Galaxy-A14'").fetchone()
    assert row["known"] == 0 and row["child_id"] is None


def test_schedule_window_math():
    s = engine.schedule_active
    assert s("thu", "22:00", "06:30", datetime(2026, 11, 5, 23, 0))       # Thu evening
    assert s("thu", "22:00", "06:30", datetime(2026, 11, 6, 6, 0))        # Fri morning, started Thu
    assert not s("thu", "22:00", "06:30", datetime(2026, 11, 6, 23, 0))   # Fri evening
    assert s("mon", "08:00", "14:00", datetime(2026, 11, 9, 9, 0))
    assert not s("mon", "08:00", "14:00", datetime(2026, 11, 9, 14, 0))
