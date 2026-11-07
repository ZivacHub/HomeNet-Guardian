# Handoff: HomeNet Guardian (folder Family_WiFi)   (updated 2026-11-07 18:00)
Git: main @ db0697f "Phase 2 closed: consent, clean-up, delete everything" · pushed: yes (https://github.com/ZivacHub/HomeNet-Guardian, PUBLIC) · uncommitted: none

## Where we are in the plan
Phase 2 of 7 — Local server + login is DONE. Steps done 16/34. Next per plan: Phase 3 gate, then 3.1 React app shell, navigation, light/dark themes.

## What we're building
A parent's dashboard for the home network that needs nothing on the child's device, running on a simulated family day, shown on a public GitHub page with screenshots, a GIF and a diagram. Goal in Ivan's words: docs/PRODUCT.md (CONFIRMED 2026-11-07).

## Last session
- Did: Phase 2 gate, decisions D18-D21 (audit skipped; app simulates TODAY on the PC clock; logged in until the browser closes; defaults accepted)
- Did: 2.1 api.py + runtime.py + schemas.py (helper, checked): 27 protected /api routes over the engine, simulation clock ticking every 5 s
- Did: 2.2 auth.py: Argon2 via pwdlib, HttpOnly SameSite=Strict session cookie, 8 h idle, 5 wrong = 1 min lock, max 2 parents; demo/demo = Mom, dad/demo = Dad
- Did: 2.3 consent.py (helper, checked): dashboard routes answer 403 consent_required until the parent confirms; family notice per child; "what it does not see" list
- Did: 2.4 retention.py: hourly 30-day clean-up on the sim clock, delete-all needs the word DELETE; 160 tests pass; real server probed (401 -> 403 -> 200; binds 127.0.0.1 only)
- Left unfinished: nothing

## Next steps (strictly in order; step 1 is where the next session starts)
1. Phase 3 gate: plain-words preview of the 8 screens, design skills (frontend-design, impeccable, design-taste-frontend, emil-design-eng) + repos search, design decisions as choice cards (look, colours, fonts), Ivan's go — done when: gate record filled in the phase file
   Read first: docs/plan/phases/03-dashboard-screens.md, docs/reference/DESIGN.md
2. 3.1 React app shell, navigation, login screen, light/dark themes (strong, here) — done when: screenshots light + dark
   Read first: docs/plan/phases/03-dashboard-screens.md, docs/reference/DESIGN.md, backend/homenet/api.py
3. 3.2 Overview screen (standard) — done when: screenshots; numbers match /api/overview
   Read first: docs/plan/phases/03-dashboard-screens.md, backend/homenet/api.py

## Waiting on the owner
- Go for Phase 3 (after the gate preview)

## Gotchas a fresh session would get wrong (max 8, only things still true)
- Repo is PUBLIC (D2): before every push list the files and scan for keys, e-mails, personal data. IDEA.md is local only (D15).
- No Claude co-author line in any commit (D4). Commits use Zivac <Gmail> (D14).
- The app simulates TODAY with the real weekday at the PC clock (D19); tests use Thursday 2026-11-05. Evening moments (21:14 explicit, 23:06 night use) only exist in the evening; raise this at the Phase 6 gate for screenshots/GIF.
- Order of API dependencies matters: auth.current_parent, then consent.require_consent, then api.get_rt (holds the runtime lock for the request). Never call a lock-taking dependency after get_rt.
- FastAPI 0.162 nests included routers: list routes via app.openapi(), not app.routes.
- Dashboard dev server proxies /api to 127.0.0.1:8000; start both with preview_start "homenet-dev". Real DB: backend/data/homenet.db (git-ignored, incl. -wal/-shm).
- Starlette warns that TestClient with httpx is deprecated (httpx2); harmless for now.

## Running / not committed
- Services running: none   ·   Not committed: none
