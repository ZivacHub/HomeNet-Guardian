# Handoff: HomeNet Guardian (folder Family_WiFi)   (updated 2026-11-07 17:00)
Git: main @ 74fbc78 "Phase 1 closed: alerts, day-in-the-life demo" · pushed: yes (https://github.com/ZivacHub/HomeNet-Guardian, PUBLIC) · uncommitted: none

## Where we are in the plan
Phase 1 of 7 — Engine + simulator is DONE. Steps done 12/34. Next per plan: Phase 2 gate, then 2.1 Local web API over the engine.

## What we're building
A parent's dashboard for the home network that needs nothing on the child's device, running on a simulated family day, shown on a public GitHub page with screenshots, a GIF and a diagram. Goal in Ivan's words: docs/PRODUCT.md (CONFIRMED 2026-11-07).

## Last session
- Did: 1.1 db.py (11 tables), 1.2 adapters (simulator family day; OpenWrt lease/query-log parsers tested on sample lines only), 1.3 categories (helper; 76,344 MIT explicit domains bundled)
- Did: 1.4 + 1.5 engine.py: rules, age profiles, schedules, pause, payment approvals (32 tests)
- Did: 1.6 alerts.py (helper, checked), 1.7 timeuse.py (helper, checked), 1.8 demo.py: `python -m homenet.demo`, proof docs/proof/day-in-the-life.txt
- Did: 109 tests pass; D14-D17 logged
- Left unfinished: nothing

## Next steps (strictly in order; step 1 is where the next session starts)
1. Phase 2 gate: plain-words preview, skills/repos search (login/password hashing libraries via context7), decisions if any, Ivan's go — done when: gate record filled in the phase file
   Read first: docs/plan/phases/02-server-login.md, docs/reference/SECURITY_CHECKLIST.md
2. 2.1 Local web API over the engine (standard) — done when: pytest with the FastAPI test client covers each endpoint
   Read first: docs/plan/phases/02-server-login.md, backend/homenet/engine.py, backend/homenet/demo.py
3. 2.2 Parent login (strong, here) — done when: no login = 401 everywhere; wrong password refused; 3rd parent refused
   Read first: docs/plan/phases/02-server-login.md, docs/reference/SECURITY_CHECKLIST.md

## Waiting on the owner
- Go for Phase 2 (after the gate preview)

## Gotchas a fresh session would get wrong (max 8, only things still true)
- Project name is HomeNet Guardian (D5); folder stays Family_WiFi (D11).
- Repo is PUBLIC (D2): before every push list the files and scan for keys, e-mails, personal data.
- IDEA.md is local only (D15): never commit it; keep the company name, dates and CV out of tracked files.
- No Claude co-author line in any commit (D4). Commits use Zivac <Gmail> (D14).
- demo.seed_family stores a placeholder password hash; real hashing + demo/demo login is step 2.2.
- alerts.py dedupes by reading the alerts table (no memory state); keep the four hook signatures engine.py calls.
- npm scripts use Windows backslash paths; start the app with preview_start "homenet-dev" (.claude/launch.json).
- The simulated day is Thursday 2026-11-05 (school night) with seed 7; tests depend on these times.

## Running / not committed
- Services running: none   ·   Not committed: none
