# HomeNet Guardian — Plan board
Status: APPROVED 2026-11-07        Plan version: 1        Last changed: 2026-11-07
Goal and non-negotiables: docs/PRODUCT.md. Every decision: docs/DECISIONS.md. Detail of each phase: docs/plan/phases/ (one file per phase).
This file stays SMALL on purpose: the tick-list, the rules and the change log. It is read at the start of every session.

## Status board
Legend: `[ ]` not started · `[~]` in progress · `[x]` done (proof in the step) · `[-]` dropped (reason in the Change log).
This board is the ONLY place that tracks progress. Tick a step in the same change set that finishes it. A script reads it
(phases = top-level lines, steps = indented lines), so keep exactly this shape. Each phase title starts with `Phase <number>`
and has a detail file `docs/plan/phases/<NN>-<name>.md` (NN = the phase number, two digits: Phase 4 -> `04-screens.md`).

- [x] Phase 0 — Foundation
  - [x] 0.1 Project files from template, CLAUDE.md filled
  - [x] 0.2 Folder layout, start command, empty dashboard opens
  - [x] 0.3 Git init, .gitignore, secrets scan, first commit
  - [x] 0.4 Public GitHub repo ZivacHub/HomeNet-Guardian, first push
- [~] Phase 1 — Engine + simulator
  - [x] 1.1 Data model and SQLite tables
  - [x] 1.2 Data source "adapter" interface + simulator adapter
  - [x] 1.3 Site categories (own list + StevenBlack explicit list)
  - [x] 1.4 Rules engine: block, categories, schedule, pause
  - [x] 1.5 Payments as approval requests
  - [ ] 1.6 Alerts: new device, night use, DNS bypass
  - [x] 1.7 Time-spent estimate
  - [ ] 1.8 "Day in the life" script + rule tests
- [ ] Phase 2 — Local server + login
  - [ ] 2.1 Local web API over the engine
  - [ ] 2.2 Parent login (up to 2 parents, demo/demo)
  - [ ] 2.3 First-start "I told my child" + notice template
  - [ ] 2.4 30-day log cleanup + "delete everything"
- [ ] Phase 3 — Dashboard screens
  - [ ] 3.1 React app shell, navigation, light/dark themes
  - [ ] 3.2 Overview screen
  - [ ] 3.3 Devices screen
  - [ ] 3.4 Live activity screen (Wireshark-style table)
  - [ ] 3.5 Where time goes screen
  - [ ] 3.6 Rules screen
  - [ ] 3.7 Payments & stores screen
  - [ ] 3.8 Settings & "What this does NOT see"
  - [ ] 3.9 Design review and polish pass
- [ ] Phase 4 — Reports
  - [ ] 4.1 Weekly and monthly report numbers
  - [ ] 4.2 Reports screen + printable HTML export
- [ ] Phase 5 — Security check
  - [ ] 5.1 Code security review + fixes
  - [ ] 5.2 Attack the running app on localhost + fixes
- [ ] Phase 6 — Showcase on GitHub
  - [ ] 6.1 How-it-works diagram
  - [ ] 6.2 Screenshots of every screen
  - [ ] 6.3 Animated GIF
  - [ ] 6.4 README: what, how it works, OpenWrt guide, limits
  - [ ] 6.5 Private-data scan, push, check the GitHub page

## Rules for this plan
- **Order:** the next step is the first unticked step of the first unfinished phase. Jumping ahead, reordering or dropping needs the owner's OK and a Change log line. Add new steps with the next free number; never renumber old ones.
- **Phase gate (before starting each phase):** (1) say in plain words what this phase builds and what the owner will be able to see/try at the end; (2) show the skills/repos search result for this phase, even when it is "nothing worth adopting, here is what I checked"; (3) put every open decision this phase needs to the owner as a choice card; (4) wait for the owner's go. Then build.
- **Phase close:** show the owner what now works (screenshot / command output), tick the phase, run the `handoff` skill.
- **Every step has a Grade** (`light` / `standard` / `strong`, in the phase file; the `delegate` skill explains them). The owner approves the grades with the plan; they are a first guess, and Claude grades the step again on the spot right before starting it. Light and standard steps may run in helpers on a cheaper model and effort; Claude checks the result before ticking.
- **Done means proven:** each step has a "Done when" and a "Test" (written in the phase file); tick only after the test ran.
- **Public repo (D2):** before every push, scan for keys, passwords, e-mails and personal data. Only simulated data ever goes in.
- **Where things go:** step detail -> the phase file. Decisions -> docs/DECISIONS.md (open ones as `[open]`). Skills list -> CLAUDE.md. Quality checklist and work split -> docs/reference/TASKS.md. Risks -> the phase file they belong to, or DECISIONS.md once the owner has to answer.

## Change log
- 2026-11-07 (Claude proposed, Ivan approved the phase list: "Yes, write the steps"): plan v1 with 7 phases; steps waiting for approval.
- 2026-11-07 (Ivan: "Approve, start Phase 0"): plan v1 approved with its grades (6 light, 17 standard, 11 strong).
