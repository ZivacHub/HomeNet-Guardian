"""The simulation clock: plays today's simulated family day in real time.

The app pretends it is the PC's real date and weekday. Every tick processes the simulated
router events between "processed up to" and now, so new lookups appear as the day goes on.
"""
from __future__ import annotations

import sqlite3
import threading
from datetime import date, datetime, time, timedelta
from typing import Callable

from . import db, demo, engine
from .adapters.simulator import SimulatorAdapter

PROCESSED_KEY = "sim_processed_until"
MAX_CATCH_UP_DAYS = 7


class Runtime:
    def __init__(self, conn: sqlite3.Connection, clock: Callable[[], datetime] = datetime.now,
                 seed: int = 7) -> None:
        self.conn = conn
        self.clock = clock
        self.seed = seed
        self.lock = threading.Lock()      # one shared sqlite connection: take this for any DB use
        self._adapters: dict[date, SimulatorAdapter] = {}
        self.started = False

    def now(self) -> datetime:
        return self.clock()

    def _adapter(self, day: date) -> SimulatorAdapter:
        if day not in self._adapters:
            self._adapters = {day: SimulatorAdapter(day, days=1, seed=self.seed)}
        return self._adapters[day]

    def _processed_until(self) -> datetime | None:
        row = self.conn.execute("SELECT value FROM settings WHERE key = ?", (PROCESSED_KEY,)).fetchone()
        return datetime.fromisoformat(row["value"]) if row else None

    def _save_processed(self, ts: datetime) -> None:
        db.set_setting(self.conn, PROCESSED_KEY, engine.iso(ts))

    def start(self) -> None:
        with self.lock:
            if self.started:
                return
            n = self.conn.execute("SELECT COUNT(*) FROM parents").fetchone()[0]
            if n == 0:
                demo.seed_family(self.conn, self.clock().date())
            self.started = True

    def tick(self) -> int:
        """Process everything up to the clock's now. Returns the number of events processed."""
        with self.lock:
            return self._tick()

    def _tick(self) -> int:
        now = self.clock().replace(microsecond=0)
        last = self._processed_until()
        if last is None:
            last = datetime.combine(now.date(), time(0, 0)) - timedelta(seconds=1)  # play today from 00:00
        if last >= now:
            return 0
        eng = engine.Engine(self.conn)
        total = 0
        day = last.date()
        earliest = now.date() - timedelta(days=MAX_CATCH_UP_DAYS)
        if day < earliest:
            day = earliest
            last = datetime.combine(day, time(0, 0)) - timedelta(seconds=1)
        while day < now.date():           # finish each old day up to 23:59:59
            end = datetime.combine(day, time(23, 59, 59))
            if last < end:
                total += eng.run(self._adapter(day), since=last, until=end)
            day += timedelta(days=1)
            last = datetime.combine(day, time(0, 0)) - timedelta(seconds=1)
        total += eng.run(self._adapter(now.date()), since=last, until=now)
        engine.expire_approvals(self.conn, now)
        self._save_processed(now)
        return total

    def close(self) -> None:
        with self.lock:
            self.conn.close()
