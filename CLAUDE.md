# HomeNet Guardian (folder: Family_WiFi)

One-line purpose: a parent's home-network dashboard that needs nothing on the child's device (network data only), running on a simulated family day. A public showcase of networking, security and management skills.

## Stack (D9; versions checked 2026-11-07, re-check with context7 before adding/upgrading)
- Backend: Python 3.11, FastAPI, SQLite (one local file), in `backend/` (package `homenet`)
- Dashboard: React + Vite + TypeScript, charts with Recharts, in `dashboard/`
- Data source: "adapter" interface; SimulatorAdapter now, OpenWrtAdapter described only (no real router, no PCAP import)
- Hosting: none. Runs locally only (127.0.0.1). Code on a PUBLIC GitHub repo ZivacHub/HomeNet-Guardian (D2)

## Commands
- Dev (both servers): `npm run dev` at the project root (filled in step 0.2)
- Test: `cd backend && .venv/Scripts/python -m pytest`
- Demo day: `python -m homenet.demo` (Phase 1)

## Conventions
- English everywhere: UI, README, code, comments (D3).
- Only simulated data goes in the repo. Before EVERY push: list the files and scan for keys, passwords, e-mails and personal data (public repo).
- Every time-spent number is labelled "estimate". Nothing claimed that is not true; unfinished parts are "in progress".
- Licence MIT. StevenBlack hosts list (MIT) is credited in README/NOTICE.

## Git attribution (asked when the project starts; the answer is in docs/DECISIONS.md D4)
- Commits and pull requests do NOT name Claude as co-author. `.claude/settings.json` sets `attribution` to empty. Never add "Co-Authored-By: Claude" or "Generated with" lines.

## Design stack (D10, chosen by Ivan 2026-11-07)
- Baseline: frontend-design
- Structure/typography/themes (light + dark switch, D7): impeccable
- Curation (anti-generic check): design-taste-frontend
- Polish and motion: emil-design-eng (+ animate / review-animations)
- Verify: playwright-cli screenshots, light and dark

## Skills (Claude must use these, not skip them)
| Skill | Used for |
|---|---|
| context7 | current docs / versions (FastAPI, Vite, React, Recharts) |
| playwright-cli | screenshots, visual checks, the GIF recording |
| frontend-design, impeccable, design-taste-frontend, emil-design-eng | dashboard UI (see Design stack) |
| dataviz | charts on "Where time goes" and Reports |
| security-review | Phase 5 code review |
| unlazy | long multi-part work |

## Plugins (enabled for this project)
- none (local-only tool: SQLite, no Supabase)

## Skill routing
- UI work: see Design stack. DB: SQLite via Python's sqlite3. Docs/versions: context7.

## Current state
- 2026-11-07: Phase 0 done (skeleton runs, public repo). Next: Phase 1 gate.

## How we work here (BUSNUS workflow v3, details in ~/.claude/CLAUDE.md)
- docs/PRODUCT.md = the goal in Ivan's words (compass). docs/plan/BOARD.md = progress, in order. docs/DECISIONS.md = what Ivan decided.
- Ivan decides; Claude proposes. Plain words, choice cards, no jargon. Phase gate before each phase.
- `/pickup` continues, `/handoff` saves, `/plan` shows/changes the plan, `/project-sync` brings this project up to the current template.

## Where things are (docs map; full list with "read when" in docs/INDEX.md)
- Always read: this file, docs/PRODUCT.md, docs/plan/BOARD.md, docs/DECISIONS.md (open part), .claude/handoff.md.
- Current phase only: docs/plan/phases/NN-name.md. The handoff's `Read first:` line names the rest for the next step.
- On demand: docs/reference/ (ARCHITECTURE, DESIGN, TESTING, TASKS, SECURITY_CHECKLIST, PRIOR_ART). History: .claude/memory.md.
- IDEA.md (root) = Ivan's original idea note from 2026-11-06. LOCAL ONLY (git-ignored, D15): never upload it, and keep job-application details (company name, dates, CV) out of every tracked file.
- Root of the project = code + this file + README.md (+ IDEA.md). New doc? Put it in docs/ and add a row to docs/INDEX.md.

## Tools (Claude starts these itself; paid ones are optional extras)
- Security: Claude's own review + local probing (free, default). Strix only if configured (paid API).
See ~/.claude/TOOLS.md.
