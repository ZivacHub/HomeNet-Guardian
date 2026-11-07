# Handoff: HomeNet Guardian (folder Family_WiFi)   (updated 2026-11-07 18:20)
Git: main @ 563be35 "Phase 3: Time, Rules, Payments and Settings screens (3.5-3.8)" · pushed: yes (https://github.com/ZivacHub/HomeNet-Guardian, PUBLIC) · uncommitted: none

## Where we are in the plan
Phase 3 of 7 — Dashboard screens, IN PROGRESS. Steps done 24/34 (3.1-3.8 done). Next per plan: 3.9 Design review and polish pass.

## What we're building
A parent's dashboard for the home network that needs nothing on the child's device, running on a simulated family day, shown on a public GitHub page with screenshots, a GIF and a diagram. Goal in Ivan's words: docs/PRODUCT.md (CONFIRMED 2026-11-07).

## Last session
- Did: Phase 3 gate: D22 "Clean product, blue" (top navigation), D23 explicit names hidden, D24 defaults
- Did: 3.1 shell (tokens light/dark, IBM Plex bundled, top bar, login, consent), DESIGN.md written; one file per screen in dashboard/src/pages
- Did: 3.2-3.8 Overview, Devices, Live activity, Time, Rules, Payments, Settings (helpers on sonnet; each checked by Claude in the browser at 1280 and 390 px, light and dark; impeccable detect clean)
- Did: live tests in the app: assign device (then undone), blocked filter, pause Ana + whole home (then resumed), approve Luka's request (now in the log as approved by Mom)
- Left unfinished: 3.9 polish; Phase 3 not closed

## Next steps (strictly in order; step 1 is where the next session starts)
1. 3.9 Design review and polish (strong, here): impeccable critique + emil-design-eng + review-animations over all screens; fix findings — done when: before/after screenshots and detect clean
   Read first: docs/plan/phases/03-dashboard-screens.md, docs/reference/DESIGN.md
2. Close Phase 3 (show Ivan, tick, handoff), then Phase 4 gate (Reports)
   Read first: docs/plan/phases/04-reports.md, backend/homenet/timeuse.py

## Waiting on the owner
- Ivan may look at the dashboard (http://127.0.0.1:5173, demo/demo) before 3.9 and name anything he wants changed

## Gotchas a fresh session would get wrong (max 8, only things still true)
- Repo is PUBLIC (D2): before every push list the files and scan for keys, e-mails, personal data. IDEA.md is local only (D15).
- No Claude co-author line in any commit (D4). Commits use Zivac <Gmail> (D14).
- The app simulates TODAY at the PC clock (D19): evening moments (21:14 explicit, 23:06 night) appear only in the evening; raise at the Phase 6 gate.
- Don't press "Delete everything" on the real demo DB: deleted past events are not replayed (processed_until stays).
- Recharts: a ReferenceArea ending on the last category needs ifOverflow="visible" to render.
- API dependency order: auth.current_parent, consent.require_consent, then api.get_rt (holds the lock). FastAPI 0.162 nests routers: list routes via app.openapi().
- Start the app with preview_start "homenet-dev"; theme is remembered in localStorage (hg-theme).

## Running / not committed
- Services running: dev servers (preview "homenet-dev") may still be running   ·   Not committed: none
