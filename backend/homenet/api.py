"""The JSON API under /api (everything here needs a logged-in parent)."""
from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from . import alerts, auth, categories as cats, db, engine, timeuse
from .runtime import Runtime
from .schemas import (ApproveBody, ChildPatch, DevicePatch, PauseBody, ResumeBody, RulePut,
                      ScheduleCreate, SchedulePatch, SettingsPatch)

router = APIRouter(prefix="/api", dependencies=[Depends(auth.current_parent)])

ONLINE_MINUTES = 10
FIXED_CATEGORIES = (cats.EXPLICIT, cats.ENCRYPTED_DNS)
SETTING_KEYS = ("retention_days", "approval_minutes_default", "bypass_minutes",
                "night_start", "night_end", "consent_confirmed")


def get_rt(request: Request):
    """The runtime, with the shared database locked for the length of the request."""
    rt: Runtime | None = request.app.state.runtime
    if rt is None:
        raise HTTPException(503, "The server is still starting")
    with rt.lock:
        yield rt


RT = Depends(get_rt)


def _rows(rows) -> list[dict]:
    return [dict(r) for r in rows]


def _day_bounds(now: datetime, day: date | None = None) -> tuple[str, str]:
    d = day or now.date()
    start = datetime.combine(d, time(0, 0))
    end = min(start + timedelta(days=1), now + timedelta(seconds=1))
    return engine.iso(start), engine.iso(max(end, start))


def _need(rt: Runtime, table: str, row_id: int, what: str):
    row = rt.conn.execute(f"SELECT * FROM {table} WHERE id = ?", (row_id,)).fetchone()
    if row is None:
        raise HTTPException(404, f"Unknown {what}")
    return row


def _need_child(rt: Runtime, child_id: int | None):
    if child_id is not None:
        _need(rt, "children", child_id, "child")


def _alert(r) -> dict:
    d = dict(r)
    d["acknowledged"] = bool(d["acknowledged"])
    return d


# --- overview ------------------------------------------------------------------------------

@router.get("/overview")
def overview(rt: Runtime = RT):
    conn, now = rt.conn, rt.now()
    day_s, day_e = _day_bounds(now)
    online_since = engine.iso(now - timedelta(minutes=ONLINE_MINUTES))
    online = conn.execute(
        "SELECT d.id, d.display_name, d.kind, d.child_id, c.name AS child_name, d.last_seen "
        "FROM devices d LEFT JOIN children c ON c.id = d.child_id "
        "WHERE d.last_seen >= ? AND d.last_seen <= ? ORDER BY d.display_name",
        (online_since, engine.iso(now))).fetchall()
    children = []
    for c in conn.execute("SELECT * FROM children ORDER BY id"):
        counts = conn.execute(
            "SELECT COUNT(*) AS n, COALESCE(SUM(q.decision = 'blocked'), 0) AS b FROM queries q "
            "JOIN devices d ON d.id = q.device_id WHERE d.child_id = ? AND q.ts >= ? AND q.ts < ?",
            (c["id"], day_s, day_e)).fetchone()
        tu = timeuse.estimate_for_child(conn, c["id"], day_s, day_e)
        children.append({
            "id": c["id"], "name": c["name"], "age_profile": c["age_profile"],
            "lookups": counts["n"], "blocked": counts["b"],
            "estimated_minutes": round(tu.total_minutes, 1),
            "top_categories": [{"category": k, "minutes": v} for k, v in list(tu.by_category.items())[:3]],
        })
    unack = conn.execute("SELECT COUNT(*) FROM alerts WHERE acknowledged = 0").fetchone()[0]
    pending = conn.execute("SELECT COUNT(*) FROM approval_requests WHERE status = 'pending'").fetchone()[0]
    return {
        "now": engine.iso(now),
        "online_devices": _rows(online),
        "online_count": len(online),
        "children": children,
        "unacknowledged_alerts": unack,
        "newest_alerts": [_alert(a) for a in alerts.list_alerts(conn)[:10]],
        "pending_approvals": pending,
        "estimate_note": timeuse.ESTIMATE_NOTE,
    }


# --- devices and children ------------------------------------------------------------------

def _device_list(rt: Runtime, device_id: int | None = None) -> list[dict]:
    now = rt.now()
    day_s, day_e = _day_bounds(now)
    online_since = engine.iso(now - timedelta(minutes=ONLINE_MINUTES))
    sql = ("SELECT d.*, c.name AS child_name, "
           "(SELECT COUNT(*) FROM queries q WHERE q.device_id = d.id AND q.ts >= ? AND q.ts < ?) AS lookups_today "
           "FROM devices d LEFT JOIN children c ON c.id = d.child_id")
    args: list = [day_s, day_e]
    if device_id is not None:
        sql += " WHERE d.id = ?"
        args.append(device_id)
    out = []
    for r in rt.conn.execute(sql + " ORDER BY d.id", args):
        d = dict(r)
        d["known"] = bool(d["known"])
        d["online"] = online_since <= d["last_seen"] <= engine.iso(now)
        out.append(d)
    return out


@router.get("/devices")
def devices(rt: Runtime = RT):
    return {"items": _device_list(rt)}


@router.patch("/devices/{device_id}")
def patch_device(device_id: int, body: DevicePatch, rt: Runtime = RT):
    _need(rt, "devices", device_id, "device")
    sets = body.model_fields_set
    if "child_id" in sets:
        _need_child(rt, body.child_id)
    updates: dict = {}
    if "display_name" in sets and body.display_name is not None:
        updates["display_name"] = body.display_name
    if "child_id" in sets:
        updates["child_id"] = body.child_id
    if "known" in sets and body.known is not None:
        updates["known"] = int(body.known)
    if updates:
        cols = ", ".join(f"{k} = ?" for k in updates)
        rt.conn.execute(f"UPDATE devices SET {cols} WHERE id = ?", (*updates.values(), device_id))
        rt.conn.commit()
    return _device_list(rt, device_id)[0]


@router.get("/children")
def children(rt: Runtime = RT):
    items = []
    for c in rt.conn.execute("SELECT * FROM children ORDER BY id"):
        d = dict(c)
        d["profile_label"] = engine.AGE_PROFILES[d["age_profile"]]["label"]
        items.append(d)
    return {"items": items}


@router.patch("/children/{child_id}")
def patch_child(child_id: int, body: ChildPatch, rt: Runtime = RT):
    _need(rt, "children", child_id, "child")
    rt.conn.execute("UPDATE children SET age_profile = ? WHERE id = ?", (body.age_profile, child_id))
    rt.conn.commit()
    d = dict(_need(rt, "children", child_id, "child"))
    d["profile_label"] = engine.AGE_PROFILES[d["age_profile"]]["label"]
    return d


# --- activity and time ---------------------------------------------------------------------

@router.get("/activity")
def activity(device_id: int | None = None, child_id: int | None = None,
             decision: Literal["allowed", "blocked"] | None = None, category: str | None = None,
             q: str | None = Query(default=None, max_length=100),
             limit: int = Query(default=100, ge=1, le=500), before_id: int | None = None,
             rt: Runtime = RT):
    where = ["q.ts <= ?"]
    args: list = [engine.iso(rt.now())]
    for cond, val in (("q.device_id = ?", device_id), ("d.child_id = ?", child_id),
                      ("q.decision = ?", decision), ("q.category = ?", category),
                      ("q.id < ?", before_id)):
        if val is not None:
            where.append(cond)
            args.append(val)
    if q:
        esc = q.lower().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        where.append("q.domain LIKE ? ESCAPE '\\'")
        args.append(f"%{esc}%")
    rows = rt.conn.execute(
        "SELECT q.*, d.display_name AS device_name, d.child_id FROM queries q "
        "JOIN devices d ON d.id = q.device_id WHERE " + " AND ".join(where) +
        " ORDER BY q.id DESC LIMIT ?", (*args, limit + 1)).fetchall()
    items = _rows(rows[:limit])
    return {"items": items, "next_before_id": items[-1]["id"] if len(rows) > limit else None}


@router.get("/timeuse")
def get_timeuse(child_id: int, date_: date | None = Query(default=None, alias="date"),
                rt: Runtime = RT):
    _need_child(rt, child_id)
    day_s, day_e = _day_bounds(rt.now(), date_)
    tu = timeuse.estimate_for_child(rt.conn, child_id, day_s, day_e)
    return {"child_id": child_id, "date": (date_ or rt.now().date()).isoformat(),
            "total_minutes": round(tu.total_minutes, 1), "by_category": tu.by_category,
            "by_site": tu.by_site, "by_hour": tu.by_hour, "sessions": tu.sessions, "note": tu.note}


# --- rules, schedules, pauses --------------------------------------------------------------

@router.get("/rules")
def get_rules(rt: Runtime = RT):
    rules = rt.conn.execute(
        "SELECT child_id, category, action FROM rules WHERE enabled = 1 ORDER BY child_id, category")
    return {"categories": [{"name": c, "fixed": c in FIXED_CATEGORIES} for c in cats.CATEGORIES],
            "rules": _rows(rules)}


@router.put("/rules")
def put_rule(body: RulePut, rt: Runtime = RT):
    _need_child(rt, body.child_id)
    try:
        engine.set_category_rule(rt.conn, body.child_id, body.category, body.action)
    except ValueError as e:
        raise HTTPException(422, str(e))
    return {"child_id": body.child_id, "category": body.category, "action": body.action}


def _schedule(rt: Runtime, sid: int) -> dict:
    d = dict(_need(rt, "schedules", sid, "schedule"))
    d["enabled"] = bool(d["enabled"])
    return d


@router.get("/schedules")
def schedules(rt: Runtime = RT):
    items = _rows(rt.conn.execute("SELECT * FROM schedules ORDER BY child_id, id"))
    for d in items:
        d["enabled"] = bool(d["enabled"])
    return {"items": items}


@router.post("/schedules", status_code=201)
def create_schedule(body: ScheduleCreate, rt: Runtime = RT):
    _need_child(rt, body.child_id)
    if body.start == body.end:
        raise HTTPException(422, "start and end must differ")
    sid = rt.conn.execute("INSERT INTO schedules(child_id, name, days, start, end) VALUES (?,?,?,?,?)",
                          (body.child_id, body.name, body.days, body.start, body.end)).lastrowid
    rt.conn.commit()
    return _schedule(rt, sid)


@router.patch("/schedules/{schedule_id}")
def patch_schedule(schedule_id: int, body: SchedulePatch, rt: Runtime = RT):
    cur = _schedule(rt, schedule_id)
    updates = {k: getattr(body, k) for k in body.model_fields_set if getattr(body, k) is not None}
    if updates.get("start", cur["start"]) == updates.get("end", cur["end"]):
        raise HTTPException(422, "start and end must differ")
    if "enabled" in updates:
        updates["enabled"] = int(updates["enabled"])
    if updates:
        cols = ", ".join(f"{k} = ?" for k in updates)
        rt.conn.execute(f"UPDATE schedules SET {cols} WHERE id = ?", (*updates.values(), schedule_id))
        rt.conn.commit()
    return _schedule(rt, schedule_id)


@router.delete("/schedules/{schedule_id}")
def delete_schedule(schedule_id: int, rt: Runtime = RT):
    _need(rt, "schedules", schedule_id, "schedule")
    rt.conn.execute("DELETE FROM schedules WHERE id = ?", (schedule_id,))
    rt.conn.commit()
    return {"deleted": schedule_id}


@router.get("/pauses")
def pauses(rt: Runtime = RT):
    now = engine.iso(rt.now())
    rows = rt.conn.execute(
        "SELECT p.*, c.name AS child_name FROM pauses p LEFT JOIN children c ON c.id = p.child_id "
        "WHERE p.started_at <= ? AND p.until_ts > ? ORDER BY p.id", (now, now))
    return {"items": _rows(rows)}


@router.post("/pause", status_code=201)
def pause(body: PauseBody, rt: Runtime = RT):
    _need_child(rt, body.child_id)
    now = rt.now()
    pid = engine.pause(rt.conn, body.child_id, now, body.minutes)
    return {"id": pid, "child_id": body.child_id, "started_at": engine.iso(now),
            "until_ts": engine.iso(now + timedelta(minutes=body.minutes))}


@router.post("/resume")
def resume(body: ResumeBody, rt: Runtime = RT):
    _need_child(rt, body.child_id)
    engine.resume(rt.conn, body.child_id, rt.now())
    return {"child_id": body.child_id, "resumed": True}


# --- approvals and alerts ------------------------------------------------------------------

def _approval(rt: Runtime, rid: int) -> dict:
    r = rt.conn.execute(
        "SELECT a.*, d.display_name AS device_name, c.name AS child_name FROM approval_requests a "
        "JOIN devices d ON d.id = a.device_id LEFT JOIN children c ON c.id = d.child_id WHERE a.id = ?",
        (rid,)).fetchone()
    if r is None:
        raise HTTPException(404, "Unknown approval request")
    return dict(r)


@router.get("/approvals")
def approvals(status: Literal["pending", "approved", "denied", "expired"] | None = None,
              rt: Runtime = RT):
    sql = ("SELECT a.*, d.display_name AS device_name, c.name AS child_name FROM approval_requests a "
           "JOIN devices d ON d.id = a.device_id LEFT JOIN children c ON c.id = d.child_id")
    args: list = []
    if status:
        sql += " WHERE a.status = ?"
        args.append(status)
    rows = rt.conn.execute(sql + " ORDER BY a.ts DESC, a.id DESC", args)
    return {"items": _rows(rows), "note": engine.PAYMENT_NOTE}


def _decide(rt: Runtime, rid: int, parent: dict | None, minutes: int | None, approve: bool) -> dict:
    _approval(rt, rid)
    pid = parent["id"] if parent else None
    try:
        if approve:
            engine.approve(rt.conn, rid, pid, rt.now(), minutes)
        else:
            engine.deny(rt.conn, rid, pid, rt.now())
    except ValueError as e:
        raise HTTPException(409, str(e))
    return _approval(rt, rid)


@router.post("/approvals/{request_id}/approve")
def approve(request_id: int, body: ApproveBody | None = None, rt: Runtime = RT,
            parent: dict | None = Depends(auth.current_parent)):
    return _decide(rt, request_id, parent, body.minutes if body else None, True)


@router.post("/approvals/{request_id}/deny")
def deny(request_id: int, rt: Runtime = RT, parent: dict | None = Depends(auth.current_parent)):
    return _decide(rt, request_id, parent, None, False)


@router.get("/alerts")
def get_alerts(unacknowledged: bool | None = None, limit: int = Query(default=200, ge=1, le=1000),
               rt: Runtime = RT):
    rows = alerts.list_alerts(rt.conn, unacknowledged_only=bool(unacknowledged))
    if unacknowledged is False:
        rows = [r for r in rows if r["acknowledged"]]
    return {"items": [_alert(r) for r in rows[:limit]]}


@router.post("/alerts/{alert_id}/ack")
def ack_alert(alert_id: int, rt: Runtime = RT):
    _need(rt, "alerts", alert_id, "alert")
    alerts.acknowledge(rt.conn, alert_id)
    return _alert(_need(rt, "alerts", alert_id, "alert"))


# --- settings and meta ---------------------------------------------------------------------

def _settings(rt: Runtime) -> dict:
    out = {k: db.get_setting(rt.conn, k) for k in SETTING_KEYS}
    for k in ("retention_days", "approval_minutes_default", "bypass_minutes"):
        out[k] = int(out[k])
    out["consent_confirmed"] = out["consent_confirmed"] == "1"
    return out


@router.get("/settings")
def get_settings(rt: Runtime = RT):
    return _settings(rt)


@router.patch("/settings")
def patch_settings(body: SettingsPatch, rt: Runtime = RT):
    for k in body.model_fields_set:
        v = getattr(body, k)
        if v is not None:
            db.set_setting(rt.conn, k, str(v))
    return _settings(rt)


@router.get("/meta")
def meta(rt: Runtime = RT):
    return {
        "categories": [{"name": c, "fixed": c in FIXED_CATEGORIES} for c in cats.CATEGORIES],
        "age_profiles": [{"age_profile": k, "label": v["label"]} for k, v in engine.AGE_PROFILES.items()],
        "payment_note": engine.PAYMENT_NOTE,
        "estimate_note": timeuse.ESTIMATE_NOTE,
        "simulated": True,
        "today": rt.now().date().isoformat(),
    }
