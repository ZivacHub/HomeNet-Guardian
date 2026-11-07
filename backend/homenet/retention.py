"""Keeping records only as long as needed.

* Automatic clean-up: lookups, alerts, finished payment requests and old pauses older than
  `retention_days` (default 30) are deleted. It runs on the simulation clock (owner decision D21).
* "Delete everything": the parent types DELETE; all activity, alerts, payment requests and pauses
  go. Accounts, children, devices, rules, schedules and settings stay, so the home keeps working.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict

from . import auth
from .db import get_setting

ACTIVITY_TABLES = ("queries", "alerts", "approval_requests", "pauses")


def _iso(ts: datetime) -> str:
    return ts.replace(microsecond=0).isoformat()


def cleanup(conn: sqlite3.Connection, now: datetime) -> dict[str, int]:
    """Delete records older than the retention setting. Returns rows deleted per table."""
    days = int(get_setting(conn, "retention_days"))
    cutoff = _iso(now - timedelta(days=days))
    deleted = {
        "queries": conn.execute("DELETE FROM queries WHERE ts < ?", (cutoff,)).rowcount,
        "alerts": conn.execute("DELETE FROM alerts WHERE ts < ?", (cutoff,)).rowcount,
        # a request still waiting for a parent is kept until someone answers it
        "approval_requests": conn.execute(
            "DELETE FROM approval_requests WHERE ts < ? AND status != 'pending'", (cutoff,)).rowcount,
        "pauses": conn.execute("DELETE FROM pauses WHERE until_ts < ?", (cutoff,)).rowcount,
    }
    conn.commit()
    return deleted


def delete_everything(conn: sqlite3.Connection) -> dict[str, int]:
    deleted = {t: conn.execute(f"DELETE FROM {t}").rowcount for t in ACTIVITY_TABLES}
    conn.commit()
    conn.execute("VACUUM")        # also clear the freed pages from the database file
    return deleted


def summary(conn: sqlite3.Connection) -> dict:
    counts = {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in ACTIVITY_TABLES}
    oldest = conn.execute("SELECT MIN(ts) FROM queries").fetchone()[0]
    return {"counts": counts, "oldest_record": oldest,
            "retention_days": int(get_setting(conn, "retention_days"))}


class DeleteAll(BaseModel):
    model_config = ConfigDict(extra="forbid")
    confirm: str


router = APIRouter(prefix="/api/data", dependencies=[Depends(auth.current_parent)])


@router.get("/summary")
def data_summary(request: Request) -> dict:
    rt = request.app.state.runtime
    with rt.lock:
        return summary(rt.conn)


@router.post("/delete-all")
def data_delete_all(body: DeleteAll, request: Request) -> dict:
    if body.confirm != "DELETE":
        raise HTTPException(422, 'Type DELETE (in capitals) to confirm.')
    rt = request.app.state.runtime
    with rt.lock:
        return {"deleted": delete_everything(rt.conn), "summary": summary(rt.conn)}
