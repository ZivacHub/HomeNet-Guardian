# Handoff: HomeNet Guardian (folder Family_WiFi)   (updated 2026-11-07 14:00)
Git: main @ see `git log -1` "Phase 0 closed: board, handoff, memory" · pushed: yes (https://github.com/ZivacHub/HomeNet-Guardian, PUBLIC) · uncommitted: none

## Where we are in the plan
Phase 0 of 7 — Foundation is DONE. Steps done 4/34. Next per plan: Phase 1 gate, then 1.1 Data model and SQLite tables.

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
1. Phase 1 gate: plain-words preview, skills/repos search for the simulator/rules engine, decisions (if any), Ivan's go — done when: gate record filled in the phase file
   Read first: docs/plan/phases/01-engine-simulator.md, docs/reference/ARCHITECTURE.md
2. 1.1 Data model and SQLite tables (strong, here) — done when: pytest writes/reads one row per table
   Read first: docs/plan/phases/01-engine-simulator.md, docs/reference/ARCHITECTURE.md
3. 1.2 Adapter interface + simulator (strong, here) — done when: same seed gives same day; every event type appears
   Read first: docs/plan/phases/01-engine-simulator.md

## Waiting on the owner
- Go for Phase 1 (after the gate preview)

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
