# Architecture

## Stack (versions confirmed 2026-11-07; re-check with context7 before installing)
- Python 3.11 + FastAPI (0.162.x) + SQLite (stdlib sqlite3), package `homenet` in `backend/`
- React 19 + Vite 8 + TypeScript in `dashboard/`; Recharts 3 for charts
- Dev: Vite dev server proxies `/api` to FastAPI on 127.0.0.1

## Flow
devices → (router: DHCP, DNS, firewall) → adapter (SimulatorAdapter now / OpenWrtAdapter later) → rules engine → SQLite → FastAPI → React dashboard

## Data model
- Defined in Phase 1 step 1.1 (see docs/plan/phases/01-engine-simulator.md).

## Key decisions
| Decision | Why | Date |
|---|---|---|
| Python + React (D9) | Ivan's choice; Python suits network tooling, React for a smooth dashboard | 2026-11-07 |
| Simulator only, OpenWrt described (D9) | Showcase only, no router available | 2026-11-07 |
| SQLite, local only | Local tool, no cloud (PRODUCT non-negotiable) | 2026-11-07 |

## Security
- Auth: parent login (Phase 2), hashed passwords, HttpOnly session cookie; server bound to 127.0.0.1.
- Secrets: none needed; `.env` never committed.
