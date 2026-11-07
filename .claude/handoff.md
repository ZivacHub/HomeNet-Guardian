# Handoff: HomeNet Guardian (folder Family_WiFi)   (updated 2026-11-07 14:00)
Git: main @ fb4edb8 "Phase 0 closed: board, handoff, memory" · pushed: yes (https://github.com/ZivacHub/HomeNet-Guardian, PUBLIC) · uncommitted: none

## Where we are in the plan
Phase 1 of 7 — Engine + simulator, IN PROGRESS. Steps done 9/34 (1.1-1.5 done). Next per plan: 1.6 Alerts.

## What we're building
A parent's dashboard for the home network that needs nothing on the child's device, running on a simulated family day, shown on a public GitHub page with screenshots, a GIF and a diagram. Goal in Ivan's words: docs/PRODUCT.md (CONFIRMED 2026-11-07).

## Last session
- Did: /new-project done; plan v1 approved ("Approve, start Phase 0"), docs/plan/BOARD.md
- Did: 0.1 CLAUDE.md, docs/INDEX.md, docs/reference/* from template v4
- Did: 0.2 backend/ (FastAPI, /api/health, pytest) + dashboard/ (React 19, Vite 8, TS); `npm run dev` starts both; page showed "Backend: connected" (helper on sonnet, checked by Claude)
- Did: 0.3 own git repo, .gitignore, MIT LICENSE, scan, first commit dac1420 (no Claude line); 0.4 public repo created and pushed
- Did: D14 commits use Gmail (Ivan's choice); D15 IDEA.md git-ignored, neutral wording for the job context in tracked files
- Left unfinished: nothing

## Next steps (strictly in order; step 1 is where the next session starts)
1. Check the step 1.7 helper's work (it was still running when the usage limit hit): backend/homenet/timeuse.py, tests/test_timeuse.py, tests/test_site_of.py, site_of() in categories.py — done when: full pytest passes and the files are reviewed, then commit
   Read first: docs/plan/phases/01-engine-simulator.md, backend/homenet/engine.py
2. 1.6 Alerts (standard): fill backend/homenet/alerts.py (stub with the contract the engine calls) — done when: each alert appears once at the expected time in the simulated day
   Read first: docs/plan/phases/01-engine-simulator.md, backend/homenet/alerts.py, backend/homenet/engine.py
3. 1.8 Day-in-the-life script (seed Mom, Dad, Ana, Luka + known devices, run SimulatorAdapter, approve Luka's 17:04 request at 17:08) and close Phase 1
   Read first: docs/plan/phases/01-engine-simulator.md, backend/homenet/adapters/simulator.py

## Waiting on the owner
- nothing (Phase 1 go given 2026-11-07)

## Gotchas a fresh session would get wrong (max 8, only things still true)
- Project name is HomeNet Guardian (D5); folder stays Family_WiFi (D11).
- Repo is PUBLIC (D2): before every push list the files and scan for keys, e-mails, personal data.
- IDEA.md is local only (D15): never commit it; keep the company name, dates and CV out of tracked files.
- No Claude co-author line in any commit (D4). Commits use Zivac <Gmail> (D14).
- Simulator only: no PCAP import, no OpenWrt VM (D9).
- npm scripts use Windows backslash paths (`backend\.venv\Scripts\python`); start the app with preview_start "homenet-dev" (.claude/launch.json).
- pytest warns that Starlette's TestClient with httpx is deprecated; harmless for now.

## Running / not committed
- Services running: none   ·   Not committed: none
