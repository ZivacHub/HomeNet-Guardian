# Handoff: HomeNet Guardian (folder Family_WiFi)   (updated 2026-11-07 18:40)
Git: main @ b68f444 "Phase 3 closed: polish pass (3.9)" · pushed: yes (https://github.com/ZivacHub/HomeNet-Guardian, PUBLIC) · uncommitted: none

## Where we are in the plan
Phase 3 of 7 — Dashboard screens is DONE. Steps done 26/34. Next per plan: Phase 4 gate (Reports), then 4.1 Weekly and monthly report numbers.

## What we're building
A parent's dashboard for the home network that needs nothing on the child's device, running on a simulated family day, shown on a public GitHub page with screenshots, a GIF and a diagram. Goal in Ivan's words: docs/PRODUCT.md (CONFIRMED 2026-11-07).

## Last session
- Did: board correction: 2.4 was done but its tick had been missed (Change log line)
- Did: 3.9 polish (Ivan: "Go ahead with polish"): press scale, hover only on mouse devices, Overview bars via transform, Payments refreshes the menu counter at once, tab title per screen, skip link, no long dashes in visible text
- Did: proof recorded in docs/plan/phases/03-dashboard-screens.md; tsc, production build, detector, dev-server log all clean
- Left unfinished: nothing in Phase 3

## Next steps (strictly in order; step 1 is where the next session starts)
1. Phase 4 gate: preview of weekly/monthly reports, search, decisions (e.g. which days count as a "week", report history: the simulator must make past days), Ivan's go — done when: gate record filled
   Read first: docs/plan/phases/04-reports.md, backend/homenet/timeuse.py, backend/homenet/runtime.py
2. 4.1 Weekly and monthly report numbers (standard) — done when: pytest on a generated month
   Read first: docs/plan/phases/04-reports.md, backend/homenet/timeuse.py
3. 4.2 Reports screen + printable export (standard) — done when: screenshot; export opens offline
   Read first: docs/plan/phases/04-reports.md, docs/reference/DESIGN.md

## Waiting on the owner
- Go for Phase 4 (after the gate preview)

## Gotchas a fresh session would get wrong (max 8, only things still true)
- Repo is PUBLIC (D2): before every push list the files and scan for keys, e-mails, personal data. IDEA.md is local only (D15).
- No Claude co-author line in any commit (D4). Commits use Zivac <Gmail> (D14).
- The app simulates TODAY at the PC clock (D19), with at most 7 days of catch-up: there is no history before the first start, so reports need the simulator to generate past days (decide at the Phase 4 gate).
- Don't press "Delete everything" on the real demo DB: deleted past events are not replayed.
- The browser console tool keeps old messages across reloads; check preview_logs and file fetch status before chasing errors.
- Recharts: a ReferenceArea ending on the last category needs ifOverflow="visible".
- API dependency order: auth.current_parent, consent.require_consent, then api.get_rt (holds the lock).
- Start the app with preview_start "homenet-dev"; theme is remembered in localStorage (hg-theme).

## Running / not committed
- Services running: dev servers (preview "homenet-dev")   ·   Not committed: none
