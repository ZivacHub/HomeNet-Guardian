# Phase 0 — Foundation
Board: docs/plan/BOARD.md lists this phase's steps and ticks. This file holds the detail.

## Purpose in plain words
Set up the project so it can be built and shared. At the end, one command starts an empty dashboard in the browser, and the public GitHub repo exists with a first upload.

## Read first (when working on this phase)
- docs/DECISIONS.md (D2 public repo, D4 no co-author, D9 stack, D11 defaults)

## Steps
**0.1 Project files from template, CLAUDE.md filled** — Grade: light (copying the template, filling facts already decided). Use: _template. Done when: CLAUDE.md (stack, skills, design stack, docs map, git attribution = none), docs/INDEX.md, docs/reference/*, .claude/{busnus.json,memory.md,settings.json} exist; TEMPLATE marker removed. Test: `node ~/.claude/hooks/pickup-context.mjs` runs without missing-file warnings. Decisions needed: none.
**0.2 Folder layout, start command, empty dashboard opens** — Grade: standard (scaffolding Python + Vite/React with current versions). Use: context7 for FastAPI/Vite. Done when: `backend/` (Python, FastAPI) and `dashboard/` (React + Vite + TypeScript) exist; one start command at the root starts both; the browser shows "HomeNet Guardian" on an empty page. Test: run the start command, playwright-cli screenshot. Decisions needed: none.
**0.3 Git init, .gitignore, secrets scan, first commit** — Grade: light (fixed procedure). Done when: Family_WiFi is its own git repo (skipped by the BUSNUS workshop repo), `.gitignore` excludes `.env`, `*.db`, `node_modules`, `.venv`, `dist`; LICENSE (MIT, Ivan's name); first commit with no Claude line. Test: the list of files to commit is shown and scanned for keys/e-mails BEFORE `git add`; `git log -1 --format=%B` has no "Claude". Decisions needed: none.
**0.4 Public GitHub repo, first push** — Grade: light (one command on Ivan's account). Done when: https://github.com/ZivacHub/HomeNet-Guardian exists as PUBLIC with a stub README. Test: `gh repo view ZivacHub/HomeNet-Guardian --json visibility` says PUBLIC; local = remote. Decisions needed: none (D2, D11).

## Risks and open points (only for this phase)
- Family_WiFi now sits inside the BUSNUS workshop git repo; the workshop's .gitignore must skip it (checked in 0.3).

## Phase gate record
- Plain-words preview shown: 2026-11-07 (phase table in chat). Skills/repos search: scaffolding only; checked versions with npm/pip/context7 (FastAPI 0.162.0, React 19.3.1, Vite 8.3.6); no skill needed beyond context7. Decisions asked: none needed (D2, D4, D9, D11 cover it). Ivan's go: 2026-11-07, "Approve, start Phase 0".
