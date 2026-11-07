# Phase 2 — Local server + login
Board: docs/plan/BOARD.md lists this phase's steps and ticks. This file holds the detail.

## Purpose in plain words
Put the brain behind a small local web server that only the parent can use. At the end you can log in (demo/demo), confirm "I told my child", and old records clean themselves up after 30 days.

## Read first (when working on this phase)
- docs/reference/SECURITY_CHECKLIST.md

## Steps
**2.1 Local web API over the engine** — Grade: standard (endpoints following one pattern). Done when: endpoints for overview, devices (incl. assign to child), activity (paged, filterable), time spent, rules, pause, approvals (list/approve/deny), alerts, settings; listens on 127.0.0.1 only. Test: pytest with the FastAPI test client.
**2.2 Parent login** — Grade: strong (login/security). Done when: up to 2 parent accounts, passwords stored hashed (never plain), session cookie (HttpOnly, SameSite=Strict); demo/demo created only in demo mode; every endpoint except login needs a login. Test: pytest: no login = 401 on every endpoint; wrong password refused; a 3rd parent refused.
**2.3 First-start honesty step** — Grade: standard (a flow + text). Done when: until the parent ticks "I told my child about this monitoring", the dashboard shows only that step; a family notice template can be copied or printed. Test: pytest: endpoints answer "consent required" before the tick.
**2.4 30-day cleanup + "delete everything"** — Grade: strong (data deletion). Done when: records older than the setting (default 30 days) are removed automatically; "delete everything" asks to type DELETE, then wipes activity, alerts and requests (keeps accounts). Test: pytest: 31-day-old records gone; after delete-all the tables are empty.

## Risks and open points (only for this phase)
- none yet

## Phase gate record
- (filled at the gate)
