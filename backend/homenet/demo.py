"""A day in the life of the demo family, printed as a readable timeline.

Run:  python -m homenet.demo            (from the backend folder)
      python -m homenet.demo --all      (every lookup, not only the interesting ones)

All data is simulated. Nothing here touches a real network.
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from collections import Counter
from datetime import date, datetime, time

from . import db, engine, timeuse
from .adapters import simulator as sim
from .adapters.simulator import SimulatorAdapter

DEMO_DAY = date(2026, 11, 5)        # a Thursday, so school-night rules apply
PARENT_APPROVES_AT = time(17, 8)    # Mom approves Luka's 17:04 purchase request
PLACEHOLDER_HASH = "demo-not-a-real-hash"   # real login (with hashing) comes in Phase 2


def seed_family(conn: sqlite3.Connection, start: date = DEMO_DAY) -> dict[str, int]:
    """Parents, children (with age-profile defaults) and the family's known devices.

    The visitor's phone is NOT added: the engine discovers it when it joins.
    Returns {"Ana": id, "Luka": id, "Mom": parent_id, "Dad": parent_id}.
    """
    ids: dict[str, int] = {}
    created = datetime.combine(start, time(0, 0)).isoformat()
    for name in sim.FAMILY_PARENTS:
        ids[name] = conn.execute(
            "INSERT INTO parents(username, display_name, password_hash, created_at) VALUES (?,?,?,?)",
            (name.lower(), name, PLACEHOLDER_HASH, created)).lastrowid
    for c in sim.FAMILY_CHILDREN:
        ids[c["name"]] = engine.add_child(conn, c["name"], c["age"], c["age_profile"])
    for d in sim.DEVICES:
        conn.execute(
            "INSERT INTO devices(mac, hostname, display_name, kind, owner, child_id, known, first_seen, last_seen) "
            "VALUES (?,?,?,?,?,?,1,?,?)",
            (d.mac, d.hostname, d.display_name, d.kind, d.owner, ids.get(d.owner)
             if d.owner in ("Ana", "Luka") else None, created, created))
    conn.commit()
    return ids


def run_day(conn: sqlite3.Connection, start: date = DEMO_DAY, seed: int = 7) -> dict[str, int]:
    """Seed the family and play the simulated day through the engine.

    Mom answers Luka's purchase request at 17:08 (approve for 30 minutes), so the timeline
    shows the whole approval story.
    """
    ids = seed_family(conn, start)
    source = SimulatorAdapter(start, days=1, seed=seed)
    eng = engine.Engine(conn)
    approve_at = datetime.combine(start, PARENT_APPROVES_AT)
    end = datetime.combine(start, time(23, 59, 59))
    eng.run(source, None, approve_at)
    pending = conn.execute("SELECT id FROM approval_requests WHERE status='pending' ORDER BY ts").fetchall()
    for row in pending:
        engine.approve(conn, row["id"], ids["Mom"], approve_at, 30)
    eng.run(source, approve_at, end)
    engine.expire_approvals(conn, end)
    return ids


# --- printing --------------------------------------------------------------------------------

INTERESTING_RULES = ("Explicit", "Encrypted", "paused", "Bedtime", "School nights", "Weekend nights",
                     "Store or payment", "Approved by", "blocked for")


def _timeline(conn: sqlite3.Connection, show_all: bool) -> list[str]:
    rows = conn.execute(
        "SELECT q.ts, d.display_name AS device, q.domain, q.category, q.decision, q.reason, q.source "
        "FROM queries q JOIN devices d ON d.id = q.device_id ORDER BY q.ts, q.id").fetchall()
    picked = [r for r in rows if show_all or r["decision"] == "blocked"
              or any(k in r["reason"] for k in INTERESTING_RULES)]
    if show_all:
        return [f"{r['ts'][11:19]}  {r['device']:<20} {r['domain']:<32} "
                f"{'BLOCKED' if r['decision'] == 'blocked' else 'allowed':<8} {r['reason']}" for r in picked]
    # fold a run of lookups from one device with the same reason (within 10 minutes) into one line
    groups: list[list[sqlite3.Row]] = []
    for r in picked:
        g = groups[-1] if groups else None
        if (g and g[-1]["device"] == r["device"] and g[-1]["reason"] == r["reason"]
                and (datetime.fromisoformat(r["ts"]) - datetime.fromisoformat(g[-1]["ts"])).seconds <= 600):
            g.append(r)
        else:
            groups.append([r])
    out = []
    for g in groups:
        first, last = g[0], g[-1]
        mark = "BLOCKED" if first["decision"] == "blocked" else "allowed"
        when = first["ts"][11:19] if len(g) == 1 else f"{first['ts'][11:16]}-{last['ts'][11:16]}"
        domains = sorted({r["domain"] for r in g})
        what = domains[0] if len(domains) == 1 else f"{len(g)} lookups ({', '.join(domains[:2])}...)"
        out.append(f"{when:<11} {first['device']:<20} {what:<44} {mark:<8} {first['reason']}")
    return out


def report(conn: sqlite3.Connection, ids: dict[str, int], start: date = DEMO_DAY,
           show_all: bool = False) -> str:
    lines: list[str] = []
    add = lines.append
    day_s = datetime.combine(start, time(0)).isoformat()
    day_e = datetime.combine(start, time(23, 59, 59)).isoformat()
    total = conn.execute("SELECT COUNT(*) FROM queries").fetchone()[0]
    blocked = conn.execute("SELECT COUNT(*) FROM queries WHERE decision='blocked'").fetchone()[0]

    add(f"HomeNet Guardian - a simulated day: {start.strftime('%A %d %B %Y')}")
    add("Family: Mom, Dad, Ana (14), Luka (9). All data is simulated.")
    add("=" * 100)
    add("")
    add("DEVICES")
    for d in conn.execute("SELECT d.*, c.name AS child FROM devices d LEFT JOIN children c ON c.id = d.child_id "
                          "ORDER BY d.known DESC, d.id"):
        who = d["child"] or d["owner"] or "unknown - not assigned"
        n = conn.execute("SELECT COUNT(*) FROM queries WHERE device_id = ?", (d["id"],)).fetchone()[0]
        add(f"  {d['display_name']:<20} {d['kind']:<8} {who:<24} first seen {d['first_seen'][11:16]}  "
            f"last seen {d['last_seen'][11:16]}  {n} lookups")
    add("")
    add(f"TIMELINE ({'every lookup' if show_all else 'blocked lookups and rule decisions; repeats folded'})")
    lines.extend("  " + t for t in _timeline(conn, show_all))
    add("")
    add("ALERTS FOR THE PARENT")
    alerts = conn.execute("SELECT * FROM alerts ORDER BY ts, id").fetchall()
    if not alerts:
        add("  (none)")
    for a in alerts:
        add(f"  {a['ts'][11:19]}  [{a['severity']:<8}] {a['message']}")
    add("")
    add("PAYMENT REQUESTS")
    for r in conn.execute("SELECT a.*, d.display_name AS device, p.display_name AS parent FROM approval_requests a "
                          "JOIN devices d ON d.id = a.device_id LEFT JOIN parents p ON p.id = a.decided_by ORDER BY a.ts"):
        extra = ""
        if r["decided_at"]:
            extra = f" by {r['parent']} at {r['decided_at'][11:16]}"
            if r["approved_until"]:
                extra += f", allowed until {r['approved_until'][11:16]}"
        add(f"  {r['ts'][11:19]}  {r['device']:<20} {r['domain']:<28} {r['status']}{extra}")
    add(f"  Note: {engine.PAYMENT_NOTE}")
    add("")
    add(f"WHERE THE CHILDREN SPENT TIME ({timeuse.ESTIMATE_NOTE})")
    for name in ("Ana", "Luka"):
        tu = timeuse.estimate_for_child(conn, ids[name], day_s, day_e)
        cats = ", ".join(f"{k} {v:.0f} min" for k, v in list(tu.by_category.items())[:5])
        sites = ", ".join(f"{k} {v:.0f}" for k, v in list(tu.by_site.items())[:5])
        add(f"  {name}: about {tu.total_minutes:.0f} min in {tu.sessions} sessions")
        add(f"     by category: {cats}")
        add(f"     top sites (min): {sites}")
    add("")
    add("SUMMARY")
    add(f"  {total} lookups, {blocked} blocked.")
    reasons = Counter(r["reason"] for r in conn.execute("SELECT reason FROM queries WHERE decision='blocked'"))
    for reason, n in reasons.most_common():
        add(f"    {n:>4}  {reason}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Print a simulated family day.")
    ap.add_argument("--all", action="store_true", help="print every lookup")
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args(argv)
    conn = db.connect(":memory:")
    ids = run_day(conn, DEMO_DAY, args.seed)
    text = report(conn, ids, DEMO_DAY, args.all)
    sys.stdout.reconfigure(encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
