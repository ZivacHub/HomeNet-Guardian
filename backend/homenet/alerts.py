"""Alerts for the parent.

Contract the engine relies on (keep these signatures):
  on_new_device(conn, device_id, ts)                      a device the home has not seen joined
  on_approval_request(conn, request_id, device_id, domain, ts)   a store/payment request is waiting
  on_query(conn, device_row, event, decision)             after every stored lookup
  check_bypass(conn, now)                                 periodic check for DNS bypass

Every alert is a row in the `alerts` table. Each kind is rate-limited per device so a
child poking at a blocked site ten times gives the parent one message, not ten.
"""
from __future__ import annotations

from datetime import date, datetime, time, timedelta

from .db import get_setting

EXPLICIT_WINDOW = timedelta(minutes=30)
VANISHED_MARK = "stopped reaching the router"
ENCRYPTED_MARK = "encrypted DNS server"


def _dt(ts) -> datetime:
    if isinstance(ts, datetime):
        return ts.replace(microsecond=0)
    return datetime.fromisoformat(str(ts)).replace(microsecond=0)


def _iso(ts) -> str:
    return _dt(ts).isoformat()


def _name(conn, device_id) -> str:
    row = conn.execute("SELECT display_name FROM devices WHERE id = ?", (device_id,)).fetchone()
    return row["display_name"] if row else "A device"


def _insert(conn, ts, kind, severity, device_id, message) -> None:
    conn.execute("INSERT INTO alerts(ts, kind, severity, device_id, message) VALUES (?,?,?,?,?)",
                 (_iso(ts), kind, severity, device_id, message))
    conn.commit()


def _exists(conn, kind, device_id, start=None, end=None, like=None) -> bool:
    """Is there already an alert of this kind for the device with ts in [start, end)?"""
    sql = "SELECT 1 FROM alerts WHERE kind = ? AND device_id = ?"
    args: list = [kind, device_id]
    if start is not None:
        sql += " AND ts >= ?"
        args.append(_iso(start))
    if end is not None:
        sql += " AND ts < ?"
        args.append(_iso(end))
    if like is not None:
        sql += " AND message LIKE ?"
        args.append(f"%{like}%")
    return conn.execute(sql + " LIMIT 1", args).fetchone() is not None


def _day_bounds(ts: datetime) -> tuple[datetime, datetime]:
    start = datetime.combine(ts.date(), time(0))
    return start, start + timedelta(days=1)


def _hm(text: str) -> time:
    h, m = text.strip().split(":")[:2]
    return time(int(h), int(m))


# --- hooks -----------------------------------------------------------------------------------

def on_new_device(conn, device_id, ts) -> None:
    row = conn.execute("SELECT display_name, known FROM devices WHERE id = ?", (device_id,)).fetchone()
    if row is None or row["known"]:
        return
    if _exists(conn, "new_device", device_id):
        return
    _insert(conn, ts, "new_device", "warning", device_id,
            f"New device joined the Wi-Fi: {row['display_name']}. Assign it to someone or mark it as known.")


def on_approval_request(conn, request_id, device_id, domain, ts) -> None:
    if _exists(conn, "approval_waiting", device_id, start=_dt(ts), end=_dt(ts) + timedelta(seconds=1),
               like=f"({domain})"):
        return
    _insert(conn, ts, "approval_waiting", "warning", device_id,
            f"{_name(conn, device_id)} wants to use a store or payment site ({domain}). Approve or deny.")


def _night_key(ts: datetime, start: time, end: time):
    """Return (night_start_dt, night_end_dt) if ts is inside the night, else None."""
    t = ts.time()
    if start > end:                      # crosses midnight
        if t >= start:
            d = ts.date()
        elif t < end:
            d = ts.date() - timedelta(days=1)
        else:
            return None
        return datetime.combine(d, start), datetime.combine(d + timedelta(days=1), end)
    if start <= t < end:
        return datetime.combine(ts.date(), start), datetime.combine(ts.date(), end)
    return None


def on_query(conn, device, event, decision) -> None:
    ts = _dt(event.ts)
    device_id = device["id"]
    name = device["display_name"]

    # a. explicit site
    if decision.rule == "explicit":
        if not _exists(conn, "explicit_blocked", device_id, start=ts - EXPLICIT_WINDOW):
            _insert(conn, ts, "explicit_blocked", "critical", device_id,
                    f"Explicit site blocked on {name}.")

    # b. night use (children's devices only)
    if (device["child_id"] is not None and decision.category not in ("system", "encrypted_dns")
            and decision.rule not in ("system", "encrypted_dns")):
        night = _night_key(ts, _hm(get_setting(conn, "night_start")), _hm(get_setting(conn, "night_end")))
        if night and not _exists(conn, "night_use", device_id, start=night[0], end=night[1]):
            suffix = " (blocked by schedule)" if decision.decision == "blocked" else ""
            _insert(conn, ts, "night_use", "info", device_id,
                    f"{name} was used at {ts.strftime('%H:%M')}, during the night.{suffix}")

    # c. encrypted DNS attempt
    if decision.rule == "encrypted_dns":
        d0, d1 = _day_bounds(ts)
        if not _exists(conn, "dns_bypass", device_id, start=d0, end=d1, like=ENCRYPTED_MARK):
            _insert(conn, ts, "dns_bypass", "warning", device_id,
                    f"{name} tried to use an encrypted DNS server ({event.domain}); it was blocked.")

    # d. lookups vanished
    if event.source == "sni":
        _check_vanished(conn, device_id, name, ts)


def _check_vanished(conn, device_id, name, ts: datetime) -> None:
    d0, d1 = _day_bounds(ts)
    if _exists(conn, "dns_bypass", device_id, start=d0, end=d1, like=VANISHED_MARK):
        return
    minutes = int(get_setting(conn, "bypass_minutes"))
    last = conn.execute(
        "SELECT MAX(ts) AS ts FROM queries WHERE device_id = ? AND source = 'dns' AND ts >= ? AND ts <= ?",
        (device_id, d0.isoformat(), ts.isoformat())).fetchone()["ts"]
    if last is not None and ts - _dt(last) < timedelta(minutes=minutes):
        return
    _insert(conn, ts, "dns_bypass", "critical", device_id,
            f"{name} is online but its site lookups {VANISHED_MARK}: it may be bypassing the filter "
            f"(encrypted DNS or VPN).")


def check_bypass(conn, now) -> None:
    now = _dt(now)
    minutes = int(get_setting(conn, "bypass_minutes"))
    since = now - timedelta(minutes=minutes)
    rows = conn.execute(
        "SELECT DISTINCT q.device_id, d.display_name FROM queries q JOIN devices d ON d.id = q.device_id "
        "WHERE q.source = 'sni' AND q.ts > ? AND q.ts <= ?", (since.isoformat(), now.isoformat())).fetchall()
    for r in rows:
        _check_vanished(conn, r["device_id"], r["display_name"], now)


# --- helpers for the API ---------------------------------------------------------------------

def list_alerts(conn, since=None, unacknowledged_only: bool = False):
    sql = "SELECT * FROM alerts WHERE 1=1"
    args: list = []
    if since is not None:
        sql += " AND ts >= ?"
        args.append(_iso(since))
    if unacknowledged_only:
        sql += " AND acknowledged = 0"
    return conn.execute(sql + " ORDER BY ts DESC, id DESC", args).fetchall()


def acknowledge(conn, alert_id) -> None:
    conn.execute("UPDATE alerts SET acknowledged = 1 WHERE id = ?", (alert_id,))
    conn.commit()
