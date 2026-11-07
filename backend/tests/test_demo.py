from homenet import db, demo


def day():
    conn = db.connect(":memory:")
    ids = demo.run_day(conn)
    return conn, ids


def test_day_plays_the_whole_story():
    conn, ids = day()
    q = lambda sql: conn.execute(sql).fetchone()[0]
    assert q("SELECT COUNT(*) FROM queries") > 2000
    assert q("SELECT COUNT(*) FROM devices") == 9
    assert q("SELECT COUNT(*) FROM devices WHERE known = 0") == 1          # the visitor's phone
    assert q("SELECT COUNT(*) FROM queries WHERE reason LIKE 'Explicit%'") == 3
    assert q("SELECT COUNT(*) FROM queries WHERE reason LIKE 'Bedtime%'") >= 4
    assert q("SELECT COUNT(*) FROM queries WHERE reason LIKE 'School nights%'") > 10
    assert q("SELECT COUNT(*) FROM queries WHERE reason LIKE 'Approved by Mom%'") == 2
    statuses = [r[0] for r in conn.execute("SELECT status FROM approval_requests ORDER BY ts")]
    assert statuses == ["expired", "pending"]                              # approved, ran out; new try waits
    # adults are never blocked by children's schedules
    assert q("SELECT COUNT(*) FROM queries q JOIN devices d ON d.id=q.device_id "
             "WHERE d.child_id IS NULL AND q.reason LIKE '%nights%'") == 0


def test_report_text_has_every_section():
    conn, ids = day()
    text = demo.report(conn, ids)
    for part in ("DEVICES", "TIMELINE", "ALERTS FOR THE PARENT", "PAYMENT REQUESTS",
                 "WHERE THE CHILDREN SPENT TIME", "SUMMARY", "Galaxy-A14",
                 "Approved by Mom until 17:38", "Explicit site (always blocked)", "Estimated"):
        assert part in text, part


def test_same_seed_same_report():
    c1, i1 = day()
    c2, i2 = day()
    assert demo.report(c1, i1) == demo.report(c2, i2)
