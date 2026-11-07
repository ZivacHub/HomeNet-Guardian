"""Estimated screen time from site lookups.

This is an ESTIMATE: a lookup shows a device touched a site, not that anyone looked at it.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterable

from .categories import ENCRYPTED_DNS, SYSTEM, site_of

ESTIMATE_NOTE = "Estimated from site lookups; not exact screen time."

IGNORED_CATEGORIES = frozenset({SYSTEM, ENCRYPTED_DNS})

# Helper domains folded into a friendly site name for display.
SITE_GROUPS = {
    "ytimg.com": "youtube.com", "googlevideo.com": "youtube.com", "ggpht.com": "youtube.com",
    "tiktokcdn.com": "tiktok.com", "tiktokcdn-us.com": "tiktok.com",
    "cdninstagram.com": "instagram.com", "fbcdn.net": "facebook.com",
    "nflxvideo.net": "netflix.com", "rbxcdn.com": "roblox.com", "scdn.co": "spotify.com",
    "sc-cdn.net": "snapchat.com", "discordapp.com": "discord.com", "discord.gg": "discord.com",
    "redd.it": "reddit.com", "licdn.com": "linkedin.com", "kastatic.org": "khanacademy.org",
    "wikimedia.org": "wikipedia.org", "whatsapp.net": "whatsapp.com",
}


@dataclass
class TimeUse:
    total_minutes: float = 0.0
    by_category: dict[str, float] = field(default_factory=dict)
    by_site: dict[str, float] = field(default_factory=dict)
    by_hour: list[float] = field(default_factory=lambda: [0.0] * 24)
    sessions: int = 0
    note: str = ESTIMATE_NOTE


def _sorted_minutes(d: dict[str, float]) -> dict[str, float]:
    items = sorted(d.items(), key=lambda kv: (-kv[1], kv[0]))
    return {k: round(v / 60, 1) for k, v in items}


def estimate(rows: Iterable, gap_minutes: float = 5) -> TimeUse:
    """Estimate time spent from lookup rows (dicts or sqlite Rows).

    Only allowed rows count; system and encrypted_dns are background traffic and ignored.
    Per device, rows are walked in time order: if the next lookup is within gap_minutes the
    gap is added to the current row's category and site; otherwise the session ends and the
    current row gets a minimum of 1 minute.

    Known limit: time on two devices at the same moment is simply added together.
    """
    per_device: dict = {}
    for r in rows:
        if r["decision"] != "allowed" or r["category"] in IGNORED_CATEGORIES:
            continue
        per_device.setdefault(r["device_id"], []).append(
            (datetime.fromisoformat(str(r["ts"])), r["category"], r["domain"]))

    gap_s = gap_minutes * 60
    cat_s: dict[str, float] = {}
    site_s: dict[str, float] = {}
    hour_s = [0.0] * 24
    sessions = 0
    total_s = 0.0

    for items in per_device.values():
        items.sort(key=lambda x: x[0])
        sessions += 1  # the first session of this device
        for i, (ts, cat, dom) in enumerate(items):
            has_next = i + 1 < len(items)
            gap = (items[i + 1][0] - ts).total_seconds() if has_next else None
            if gap is not None and gap <= gap_s:
                secs = gap
            else:
                secs = 60.0
                if has_next:
                    sessions += 1  # a new session starts after this one ended
            site = site_of(dom)
            site = SITE_GROUPS.get(site, site)
            cat_s[cat] = cat_s.get(cat, 0.0) + secs
            site_s[site] = site_s.get(site, 0.0) + secs
            hour_s[ts.hour] += secs
            total_s += secs

    return TimeUse(
        total_minutes=round(total_s / 60, 1),
        by_category=_sorted_minutes(cat_s),
        by_site=_sorted_minutes(site_s),
        by_hour=[round(h / 60, 1) for h in hour_s],
        sessions=sessions,
    )


_COLS = "q.ts, q.device_id, q.domain, q.category, q.decision"


def estimate_for_child(conn: sqlite3.Connection, child_id: int, start_ts: str, end_ts: str,
                       gap_minutes: float = 5) -> TimeUse:
    """Estimate for all devices of a child in [start_ts, end_ts). See estimate() for limits."""
    rows = conn.execute(
        f"SELECT {_COLS} FROM queries q JOIN devices d ON d.id = q.device_id "
        "WHERE d.child_id = ? AND q.ts >= ? AND q.ts < ? ORDER BY q.ts",
        (child_id, start_ts, end_ts)).fetchall()
    return estimate(rows, gap_minutes)


def estimate_for_device(conn: sqlite3.Connection, device_id: int, start_ts: str, end_ts: str,
                        gap_minutes: float = 5) -> TimeUse:
    """Estimate for one device in [start_ts, end_ts)."""
    rows = conn.execute(
        f"SELECT {_COLS} FROM queries q WHERE q.device_id = ? AND q.ts >= ? AND q.ts < ? "
        "ORDER BY q.ts", (device_id, start_ts, end_ts)).fetchall()
    return estimate(rows, gap_minutes)
