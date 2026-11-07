"""First-start honesty step.

Before the dashboard shows anything, a parent confirms they told the child about the monitoring,
and the app offers a ready-made family notice plus an honest list of what it cannot see.

Contract for the API:
  require_consent(request)  FastAPI dependency: raises 403 {"code": "consent_required", ...}
                            until a parent has confirmed.
  router                    /api/consent (all routes need a logged-in parent)
"""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, StrictBool

from . import auth
from .db import get_setting, set_setting

NOTICE_TEMPLATE = """\
Hi {child_name},

We want you to know how our home Wi-Fi is looked after. {parent_names} can see, in a dashboard, \
which website names the devices on our home network ask for, when they ask, and roughly how long \
that adds up to (the time is an estimate, not an exact stopwatch).

It does NOT see your messages, photos, passwords or what is on a page. It does not work when a \
phone uses mobile data instead of our Wi-Fi.

Some sites are blocked because they are explicit. Shops and payment sites need a parent's OK \
first. The records are deleted after {retention_days} days.

Nothing is installed on your phone or computer. This is only about the home network.

You can always talk to us about it: ask us anything, tell us if a block seems unfair, or tell us \
if something does not feel right.
"""

WHAT_IT_DOES_NOT_SEE: list[dict[str, str]] = [
    {"title": "Messages and page content",
     "text": "It never sees what you write, send or read, only the name of a site a device asked for."},
    {"title": "Mobile data (4G/5G)",
     "text": "When a phone uses mobile data instead of the home Wi-Fi, nothing is visible."},
    {"title": "VPNs",
     "text": "A VPN hides site names from the home network, so those lookups cannot be seen."},
    {"title": "Encrypted DNS (\"private DNS\")",
     "text": "If a device hides its lookups this way they vanish from the data; the app warns "
             "when lookups suddenly disappear."},
    {"title": "Encrypted site names (ECH)",
     "text": "Newer browsers can encrypt even the name of the site, which then cannot be seen."},
    {"title": "Devices that change their address",
     "text": "Phones that use a random address (random MAC) are recognised by their device name "
             "when possible, but not always."},
    {"title": "Time spent is an estimate",
     "text": "Minutes are worked out from lookups, so they are a rough guide, not exact."},
]


def _opt(conn, key: str) -> str:
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else ""


def _rt(request: Request):
    rt = request.app.state.runtime
    if rt is None:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "The server is still starting")
    return rt


def require_consent(request: Request) -> None:
    rt = _rt(request)
    with rt.lock:
        confirmed = get_setting(rt.conn, "consent_confirmed")
    if confirmed != "1":
        raise HTTPException(status.HTTP_403_FORBIDDEN, {
            "code": "consent_required",
            "message": "Confirm that your child knows about this monitoring before using the dashboard.",
        })


def _join_names(names: list[str]) -> str:
    if not names:
        return "Your parents"
    if len(names) == 1:
        return names[0]
    return " and ".join(names)


def _state(request: Request) -> dict:
    rt = _rt(request)
    with rt.lock:
        conn = rt.conn
        confirmed = get_setting(conn, "consent_confirmed") == "1"
        by_id = _opt(conn, "consent_by") if confirmed else ""
        at = _opt(conn, "consent_at") if confirmed else ""
        retention = get_setting(conn, "retention_days")
        parents = [r["display_name"] for r in
                   conn.execute("SELECT display_name FROM parents ORDER BY id").fetchall()]
        children = conn.execute("SELECT id, name FROM children ORDER BY id").fetchall()
        by_name = None
        if confirmed and by_id.isdigit():
            row = conn.execute("SELECT display_name FROM parents WHERE id = ?", (int(by_id),)).fetchone()
            by_name = row["display_name"] if row else None
    parent_names = _join_names(parents)
    return {
        "confirmed": confirmed,
        "confirmed_by": by_name,
        "confirmed_at": at or None,
        "notice": [
            {"child_id": c["id"], "child_name": c["name"],
             "text": NOTICE_TEMPLATE.format(child_name=c["name"], parent_names=parent_names,
                                            retention_days=retention)}
            for c in children
        ],
        "does_not_see": WHAT_IT_DOES_NOT_SEE,
    }


class ConsentIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    told_child: StrictBool


router = APIRouter(prefix="/api/consent")


@router.get("")
def get_consent(request: Request, parent: dict = Depends(auth.current_parent)) -> dict:
    return _state(request)


@router.post("")
def confirm_consent(body: ConsentIn, request: Request,
                    parent: dict = Depends(auth.current_parent)) -> dict:
    if body.told_child is not True:
        raise HTTPException(422, "told_child must be true")
    rt = _rt(request)
    with rt.lock:
        set_setting(rt.conn, "consent_confirmed", "1")
        set_setting(rt.conn, "consent_by", str(parent["id"]))
        set_setting(rt.conn, "consent_at", datetime.now().replace(microsecond=0).isoformat())
    return _state(request)


@router.post("/withdraw")
def withdraw_consent(request: Request, parent: dict = Depends(auth.current_parent)) -> dict:
    rt = _rt(request)
    with rt.lock:
        set_setting(rt.conn, "consent_confirmed", "0")
    return _state(request)


@router.get("/does-not-see")
def does_not_see(parent: dict = Depends(auth.current_parent)) -> list[dict[str, str]]:
    return WHAT_IT_DOES_NOT_SEE
