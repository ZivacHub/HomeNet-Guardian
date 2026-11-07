"""The rules engine: decides, for every site lookup, whether it is allowed and why.

Order of checks (first match wins):
  1. Explicit sites                     -> always blocked, for every device in the home
  2. Known encrypted-DNS servers        -> always blocked (they would hide lookups from the filter)
  3. Background system traffic          -> always allowed (time sync, connectivity checks)
  4. Pause (this child, or whole home)  -> blocked
  5. A no-internet schedule (children)  -> blocked, e.g. bedtime
  6. Stores and payments (children)     -> blocked until a parent approves for N minutes
  7. Category rule (child, else home)   -> blocked / allowed
  8. Otherwise                          -> allowed

Payment control here works on site names only. Real purchase control lives in the phone's own
family settings (Apple Family Sharing "Ask to Buy", Google Family Link); the app says so.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta

from . import alerts, categories as cats
from .adapters.base import DeviceSeen, NetEvent
from .db import get_setting

PAYMENT_NOTE = ("Store and payment blocking works on site names only. Real purchase control "
                "lives in the phone's family settings (Apple Ask to Buy, Google Family Link).")

DAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
SCHOOL_NIGHTS = "sun,mon,tue,wed,thu"
WEEKEND_NIGHTS = "fri,sat"

# Defaults a parent gets when a child is added with an age profile. Editable afterwards.
AGE_PROFILES: dict[int, dict] = {
    8: {
        "label": "Up to 9",
        "blocked_categories": [cats.SOCIAL, cats.MESSAGING, cats.SHOPPING],
        "schedules": [("Bedtime", ",".join(DAYS), "20:30", "07:00")],
    },
    13: {
        "label": "10 to 13+",
        "blocked_categories": [],
        "schedules": [("School nights", SCHOOL_NIGHTS, "22:00", "06:30"),
                      ("Weekend nights", WEEKEND_NIGHTS, "23:30", "07:00")],
    },
    16: {
        "label": "16+",
        "blocked_categories": [],
        "schedules": [("School nights", SCHOOL_NIGHTS, "23:30", "06:30")],
    },
}

ALWAYS_ALLOWED = {cats.SYSTEM}


def iso(ts: datetime) -> str:
    return ts.replace(microsecond=0).isoformat()


def hhmm(ts_text: str) -> str:
    return ts_text[11:16]


@dataclass(frozen=True)
class Decision:
    decision: str          # "allowed" | "blocked"
    reason: str
    category: str
    rule: str              # machine name of the check that decided: explicit, encrypted_dns, ...
    request_id: int | None = None   # set when a payment approval request was created/reused


# --- children and age profiles ----------------------------------------------------------

def add_child(conn: sqlite3.Connection, name: str, age: int, age_profile: int) -> int:
    """Create a child and apply the defaults of the age profile."""
    if age_profile not in AGE_PROFILES:
        raise ValueError(f"age_profile must be one of {sorted(AGE_PROFILES)}")
    cid = conn.execute("INSERT INTO children(name, age, age_profile) VALUES (?, ?, ?)",
                       (name, age, age_profile)).lastrowid
    prof = AGE_PROFILES[age_profile]
    for cat in prof["blocked_categories"]:
        set_category_rule(conn, cid, cat, "block")
    for sname, days, start, end in prof["schedules"]:
        conn.execute("INSERT INTO schedules(child_id, name, days, start, end) VALUES (?,?,?,?,?)",
                     (cid, sname, days, start, end))
    conn.commit()
    return cid


def set_category_rule(conn: sqlite3.Connection, child_id: int | None, category: str,
                      action: str | None) -> None:
    """action 'block' / 'allow', or None to remove the rule (fall back to home / default)."""
    if category not in cats.CATEGORIES:
        raise ValueError(f"unknown category {category!r}")
    if category in (cats.EXPLICIT, cats.ENCRYPTED_DNS):
        raise ValueError(f"{category} is always blocked and cannot be changed")
    if child_id is None:
        conn.execute("DELETE FROM rules WHERE child_id IS NULL AND category = ?", (category,))
    else:
        conn.execute("DELETE FROM rules WHERE child_id = ? AND category = ?", (child_id, category))
    if action is not None:
        if action not in ("block", "allow"):
            raise ValueError("action must be 'block' or 'allow'")
        conn.execute("INSERT INTO rules(child_id, category, action) VALUES (?,?,?)",
                     (child_id, category, action))
    conn.commit()


def pause(conn: sqlite3.Connection, child_id: int | None, now: datetime, minutes: int) -> int:
    """One-click pause for a child (or the whole home when child_id is None)."""
    pid = conn.execute("INSERT INTO pauses(child_id, started_at, until_ts) VALUES (?,?,?)",
                       (child_id, iso(now), iso(now + timedelta(minutes=minutes)))).lastrowid
    conn.commit()
    return pid


def resume(conn: sqlite3.Connection, child_id: int | None, now: datetime) -> None:
    """End any running pause for that child (or the home) right now."""
    if child_id is None:
        conn.execute("UPDATE pauses SET until_ts = ? WHERE child_id IS NULL AND until_ts > ?",
                     (iso(now), iso(now)))
    else:
        conn.execute("UPDATE pauses SET until_ts = ? WHERE child_id = ? AND until_ts > ?",
                     (iso(now), child_id, iso(now)))
    conn.commit()


# --- schedules -----------------------------------------------------------------------------

def schedule_active(days: str, start: str, end: str, ts: datetime) -> bool:
    """Is ts inside the window? `days` names the day a window starts on; it may cross midnight."""
    day_set = {d.strip() for d in days.split(",") if d.strip()}
    t = ts.strftime("%H:%M")
    today = DAYS[ts.weekday()]
    yesterday = DAYS[(ts.weekday() - 1) % 7]
    if start <= end:                                 # same-day window, e.g. 08:00-14:00
        return today in day_set and start <= t < end
    # crosses midnight, e.g. 22:00-06:30: evening part today, morning part from yesterday's start
    return (today in day_set and t >= start) or (yesterday in day_set and t < end)


# --- payment approvals -----------------------------------------------------------------

def _active_approval(conn: sqlite3.Connection, device_id: int, ts: datetime) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT a.*, p.display_name AS parent FROM approval_requests a "
        "LEFT JOIN parents p ON p.id = a.decided_by "
        "WHERE a.device_id = ? AND a.status = 'approved' AND a.decided_at <= ? AND a.approved_until > ? "
        "ORDER BY a.approved_until DESC LIMIT 1",
        (device_id, iso(ts), iso(ts))).fetchone()


def _open_request(conn: sqlite3.Connection, device_id: int, domain: str, ts: datetime) -> tuple[int, bool]:
    """Reuse the device's pending request, or create one. Returns (id, created)."""
    row = conn.execute("SELECT id FROM approval_requests WHERE device_id = ? AND status = 'pending' "
                       "ORDER BY ts DESC LIMIT 1", (device_id,)).fetchone()
    if row:
        return row["id"], False
    rid = conn.execute("INSERT INTO approval_requests(ts, device_id, domain, status) VALUES (?,?,?,'pending')",
                       (iso(ts), device_id, domain)).lastrowid
    return rid, True


def approve(conn: sqlite3.Connection, request_id: int, parent_id: int | None, now: datetime,
            minutes: int | None = None) -> None:
    """A parent allows store/payment sites on that device for `minutes` (default from settings)."""
    if minutes is None:
        minutes = int(get_setting(conn, "approval_minutes_default"))
    if not 1 <= minutes <= 24 * 60:
        raise ValueError("minutes must be between 1 and 1440")
    cur = conn.execute(
        "UPDATE approval_requests SET status='approved', decided_by=?, decided_at=?, approved_until=? "
        "WHERE id=? AND status='pending'",
        (parent_id, iso(now), iso(now + timedelta(minutes=minutes)), request_id))
    if cur.rowcount != 1:
        raise ValueError("request is not pending")
    conn.commit()


def deny(conn: sqlite3.Connection, request_id: int, parent_id: int | None, now: datetime) -> None:
    cur = conn.execute("UPDATE approval_requests SET status='denied', decided_by=?, decided_at=? "
                       "WHERE id=? AND status='pending'", (parent_id, iso(now), request_id))
    if cur.rowcount != 1:
        raise ValueError("request is not pending")
    conn.commit()


def expire_approvals(conn: sqlite3.Connection, now: datetime) -> int:
    """Mark approvals whose time ran out as expired (for the decision log)."""
    cur = conn.execute("UPDATE approval_requests SET status='expired' "
                       "WHERE status='approved' AND approved_until <= ?", (iso(now),))
    conn.commit()
    return cur.rowcount


# --- the engine ------------------------------------------------------------------------------

class Engine:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    # devices
    def sync_devices(self, seen: list[DeviceSeen]) -> list[int]:
        """Register devices from the router's lease list. Returns ids of devices new to the home."""
        return [d_id for d_id, new in (self._device_for(d.mac, d.hostname, d.first_seen, d.kind_hint)
                                       for d in seen) if new]

    def _device_for(self, mac: str, hostname: str, ts: datetime,
                    kind: str = "unknown") -> tuple[int, bool]:
        mac = mac.lower()
        row = self.conn.execute("SELECT id FROM devices WHERE mac = ?", (mac,)).fetchone()
        if row:
            return row["id"], False
        if hostname:
            # Phones use a new random MAC per network or over time; the hostname usually stays.
            row = self.conn.execute("SELECT id FROM devices WHERE hostname = ? AND hostname != ''",
                                    (hostname,)).fetchone()
            if row:
                self.conn.execute("UPDATE devices SET mac = ? WHERE id = ?", (mac, row["id"]))
                self.conn.commit()
                return row["id"], False
        did = self.conn.execute(
            "INSERT INTO devices(mac, hostname, display_name, kind, known, first_seen, last_seen) "
            "VALUES (?,?,?,?,0,?,?)",
            (mac, hostname, hostname or f"Unknown device {mac[-5:]}", kind, iso(ts), iso(ts))).lastrowid
        self.conn.commit()
        alerts.on_new_device(self.conn, did, ts)
        return did, True

    # decisions
    def decide(self, device: sqlite3.Row, domain: str, ts: datetime) -> Decision:
        conn = self.conn
        category = cats.categorize(domain)
        child_id = device["child_id"]
        child = None
        if child_id is not None:
            child = conn.execute("SELECT * FROM children WHERE id = ?", (child_id,)).fetchone()

        if category == cats.EXPLICIT:
            return Decision("blocked", "Explicit site (always blocked)", category, "explicit")
        if category == cats.ENCRYPTED_DNS:
            return Decision("blocked", "Encrypted DNS server (blocked so the filter keeps working)",
                            category, "encrypted_dns")
        if category in ALWAYS_ALLOWED:
            return Decision("allowed", "Background system traffic", category, "system")

        now = iso(ts)
        p = conn.execute(
            "SELECT * FROM pauses WHERE started_at <= ? AND until_ts > ? AND (child_id IS NULL OR child_id IS ?) "
            "ORDER BY child_id IS NULL LIMIT 1", (now, now, child_id)).fetchone()
        if p is not None:
            who = "whole home" if p["child_id"] is None else child["name"]
            return Decision("blocked", f"Internet paused ({who}) until {hhmm(p['until_ts'])}", category, "pause")

        if child is not None:
            for s in conn.execute("SELECT * FROM schedules WHERE child_id = ? AND enabled = 1", (child_id,)):
                if schedule_active(s["days"], s["start"], s["end"], ts):
                    return Decision("blocked", f"{s['name']} {s['start']}-{s['end']}", category, "schedule")

            if category == cats.PAYMENTS:
                a = _active_approval(conn, device["id"], ts)
                if a is not None:
                    by = a["parent"] or "a parent"
                    return Decision("allowed", f"Approved by {by} until {hhmm(a['approved_until'])}",
                                    category, "approval")
                rid, created = _open_request(conn, device["id"], domain, ts)
                conn.commit()
                if created:
                    alerts.on_approval_request(conn, rid, device["id"], domain, ts)
                return Decision("blocked", "Store or payment: waiting for a parent's approval",
                                category, "payment", rid)

        rule = None
        if child_id is not None:
            rule = conn.execute("SELECT * FROM rules WHERE child_id = ? AND category = ? AND enabled = 1",
                                (child_id, category)).fetchone()
        if rule is None:
            rule = conn.execute("SELECT * FROM rules WHERE child_id IS NULL AND category = ? AND enabled = 1",
                                (category,)).fetchone()
        if rule is not None and rule["action"] == "block":
            who = child["name"] if rule["child_id"] is not None else "the whole home"
            return Decision("blocked", f"{category.replace('_', ' ').capitalize()} blocked for {who}",
                            category, "category")
        if rule is not None:
            return Decision("allowed", f"{category.replace('_', ' ').capitalize()} allowed by rule",
                            category, "category")
        return Decision("allowed", "No rule applies", category, "default")

    def process(self, event: NetEvent, hostname: str = "") -> Decision:
        """Decide one event from the adapter, store it, update the device and raise alerts."""
        device_id, _ = self._device_for(event.mac, hostname, event.ts)
        self.conn.execute("UPDATE devices SET last_seen = ? WHERE id = ? AND last_seen < ?",
                          (iso(event.ts), device_id, iso(event.ts)))
        device = self.conn.execute("SELECT * FROM devices WHERE id = ?", (device_id,)).fetchone()
        d = self.decide(device, event.domain, event.ts)
        self.conn.execute(
            "INSERT INTO queries(ts, device_id, domain, source, bytes, category, decision, reason) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (iso(event.ts), device_id, event.domain.lower(), event.source, event.bytes,
             d.category, d.decision, d.reason))
        self.conn.commit()
        alerts.on_query(self.conn, device, event, d)
        return d

    def run(self, source, since: datetime | None = None, until: datetime | None = None) -> int:
        """Pull devices and events from an adapter and process them. Returns events processed."""
        hostnames = {d.mac.lower(): d.hostname for d in source.devices()}
        self.sync_devices(source.devices())
        n = 0
        for e in source.queries(since, until):
            self.process(e, hostnames.get(e.mac.lower(), ""))
            n += 1
        alerts.check_bypass(self.conn, until or datetime.now())
        return n
