"""SQLite storage for HomeNet Guardian.

One local database file holds everything. Times are stored as ISO-8601 text in the
home's local time ("2026-11-07T21:15:03"), which sorts correctly as text.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA_VERSION = 1

SCHEMA = """
CREATE TABLE IF NOT EXISTS parents (
    id            INTEGER PRIMARY KEY,
    username      TEXT NOT NULL UNIQUE,
    display_name  TEXT NOT NULL,
    password_hash TEXT NOT NULL,          -- never the plain password
    created_at    TEXT NOT NULL
);

-- A child and the age profile that sets default rules (8 / 13 / 16).
CREATE TABLE IF NOT EXISTS children (
    id          INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    age         INTEGER NOT NULL,
    age_profile INTEGER NOT NULL CHECK (age_profile IN (8, 13, 16))
);

-- Everything that joined the home network. Recognised by MAC address and, because new
-- phones randomise their MAC, also by hostname (see engine).
CREATE TABLE IF NOT EXISTS devices (
    id           INTEGER PRIMARY KEY,
    mac          TEXT NOT NULL UNIQUE,
    hostname     TEXT NOT NULL DEFAULT '',
    display_name TEXT NOT NULL,
    kind         TEXT NOT NULL DEFAULT 'unknown',   -- phone, tablet, laptop, tv, console, unknown
    owner        TEXT NOT NULL DEFAULT '',          -- free text such as "Mom" for adults
    child_id     INTEGER REFERENCES children(id) ON DELETE SET NULL,
    known        INTEGER NOT NULL DEFAULT 0,        -- 1 once a parent has confirmed it
    first_seen   TEXT NOT NULL,
    last_seen    TEXT NOT NULL
);

-- One row per site-name lookup the router saw (DNS) or per TLS connection name (SNI).
CREATE TABLE IF NOT EXISTS queries (
    id        INTEGER PRIMARY KEY,
    ts        TEXT NOT NULL,
    device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    domain    TEXT NOT NULL,
    source    TEXT NOT NULL CHECK (source IN ('dns', 'sni')),
    bytes     INTEGER NOT NULL DEFAULT 0,
    category  TEXT NOT NULL,
    decision  TEXT NOT NULL CHECK (decision IN ('allowed', 'blocked')),
    reason    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_queries_ts ON queries(ts);
CREATE INDEX IF NOT EXISTS idx_queries_device_ts ON queries(device_id, ts);

-- Category blocks. child_id NULL = applies to the whole home.
CREATE TABLE IF NOT EXISTS rules (
    id       INTEGER PRIMARY KEY,
    child_id INTEGER REFERENCES children(id) ON DELETE CASCADE,
    category TEXT NOT NULL,
    action   TEXT NOT NULL CHECK (action IN ('block', 'allow')),
    enabled  INTEGER NOT NULL DEFAULT 1,
    UNIQUE (child_id, category)
);

-- "No internet" time windows, e.g. school nights 22:00-07:00. days = comma list mon..sun
-- naming the day the window STARTS on (a window may run past midnight).
CREATE TABLE IF NOT EXISTS schedules (
    id       INTEGER PRIMARY KEY,
    child_id INTEGER REFERENCES children(id) ON DELETE CASCADE,
    name     TEXT NOT NULL,
    days     TEXT NOT NULL,
    start    TEXT NOT NULL,   -- HH:MM
    end      TEXT NOT NULL,   -- HH:MM
    enabled  INTEGER NOT NULL DEFAULT 1
);

-- One-click "pause internet". child_id NULL = whole home.
CREATE TABLE IF NOT EXISTS pauses (
    id         INTEGER PRIMARY KEY,
    child_id   INTEGER REFERENCES children(id) ON DELETE CASCADE,
    started_at TEXT NOT NULL,
    until_ts   TEXT NOT NULL
);

-- A store or payment site was tried; a parent approves it for some minutes or denies it.
CREATE TABLE IF NOT EXISTS approval_requests (
    id             INTEGER PRIMARY KEY,
    ts             TEXT NOT NULL,
    device_id      INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    domain         TEXT NOT NULL,
    status         TEXT NOT NULL CHECK (status IN ('pending', 'approved', 'denied', 'expired')),
    decided_by     INTEGER REFERENCES parents(id) ON DELETE SET NULL,
    decided_at     TEXT,
    approved_until TEXT
);

CREATE TABLE IF NOT EXISTS alerts (
    id           INTEGER PRIMARY KEY,
    ts           TEXT NOT NULL,
    kind         TEXT NOT NULL,     -- new_device, explicit_blocked, night_use, approval_waiting, dns_bypass
    severity     TEXT NOT NULL CHECK (severity IN ('info', 'warning', 'critical')),
    device_id    INTEGER REFERENCES devices(id) ON DELETE CASCADE,
    message      TEXT NOT NULL,
    acknowledged INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_alerts_ts ON alerts(ts);

CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""

DEFAULT_SETTINGS = {
    "schema_version": str(SCHEMA_VERSION),
    "retention_days": "30",
    "consent_confirmed": "0",           # parent confirmed they told the child
    "approval_minutes_default": "30",
    "bypass_minutes": "10",             # traffic without DNS for this long = possible bypass
    "night_start": "23:00",
    "night_end": "06:00",
}

TABLES = (
    "parents", "children", "devices", "queries", "rules", "schedules",
    "pauses", "approval_requests", "alerts", "settings",
)


def connect(path: str | Path = ":memory:") -> sqlite3.Connection:
    """Open (and create if needed) the database, with the schema and default settings."""
    conn = sqlite3.connect(str(path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    if str(path) != ":memory:":
        conn.execute("PRAGMA journal_mode = WAL")
    conn.executescript(SCHEMA)
    conn.executemany(
        "INSERT OR IGNORE INTO settings(key, value) VALUES (?, ?)", DEFAULT_SETTINGS.items()
    )
    conn.commit()
    return conn


def get_setting(conn: sqlite3.Connection, key: str) -> str:
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    if row is None:
        return DEFAULT_SETTINGS[key]
    return row["value"]


def set_setting(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute(
        "INSERT INTO settings(key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, value),
    )
    conn.commit()
