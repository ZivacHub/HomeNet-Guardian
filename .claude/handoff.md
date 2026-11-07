# Handoff: HomeNet Guardian (folder Family_WiFi)   (updated 2026-11-07 19:10)
Git: main @ 2d108cc "Phase 6 closed: vertical diagram, board and notes" · pushed: yes (https://github.com/ZivacHub/HomeNet-Guardian, PUBLIC) · uncommitted: none

## Where we are in the plan
Phases 0, 1, 2, 3 and 6 are DONE (Phase 6 moved ahead on Ivan's request, Change log). Steps done 31/34. Next per plan: Phase 4 gate is recorded (D25); start 4.1 Weekly and monthly report numbers.

## What we're building
A parent's dashboard for the home network that needs nothing on the child's device, running on a simulated family day, shown on a public GitHub page with screenshots, a GIF and a diagram. Goal in Ivan's words: docs/PRODUCT.md (CONFIRMED 2026-11-07).

## Last session
- Did: D25 (4-week history), D26 (separate picture run), D27 (README up first, Ivan reviews after); Ivan: "Focus on finishing the git look and images" -> Phase 6 first
- Did: /api/clock so the top bar shows the simulated time; env switches HOMENET_DB / HOMENET_CLOCK_START / HOMENET_CLOCK_SPEED, HG_API proxy target; launch configs pictures-api, pictures-web, gif-api
- Did: 14 screenshots + demo.gif in docs/screenshots, README rewritten (Mermaid diagram, screens table, does-not-see, OpenWrt plan, run, credits), repo topics; live page checked (15/15 images, diagram renders)
- Left unfinished: Phase 4 (Reports) and Phase 5 (security); README says both are in progress

## Next steps (strictly in order; step 1 is where the next session starts)
1. 4.1 Weekly and monthly report numbers + 4-week history at first start (D25: past days' requests answered, past alerts marked seen) — done when: pytest on a generated month
   Read first: docs/plan/phases/04-reports.md, backend/homenet/runtime.py
2. 4.2 Reports screen + printable HTML export — done when: screenshot; export opens offline; retake docs/screenshots with a reports picture
   Read first: docs/plan/phases/04-reports.md, docs/reference/DESIGN.md
3. Phase 5: 5.1 code security review, 5.2 probes on 127.0.0.1 — done when: findings and fixes in docs/reference/SECURITY_CHECKLIST.md; then update README status lines
   Read first: docs/plan/phases/05-security.md, docs/reference/SECURITY_CHECKLIST.md

## Waiting on the owner
- README review on the live GitHub page (D27): any wording Ivan wants changed

## Gotchas a fresh session would get wrong (max 8, only things still true)
- Repo is PUBLIC (D2): before every push list the files and scan for keys, e-mails, personal data. IDEA.md is local only (D15).
- No Claude co-author line in any commit (D4). Commits use Zivac <Gmail> (D14).
- Normal app follows the PC clock (D19); picture runs use their own DB and a set clock (D26). Delete backend/data/gif.db before a new GIF run (clock starts at server start).
- Pillow for the GIF lives in a throwaway venv in the scratchpad, not in requirements.
- Don't press "Delete everything" on the real demo DB: deleted past events are not replayed.
- The browser console tool keeps old messages across reloads; check preview_logs and fetch status.
- Chained `&&` commands stop silently when a step fails (e.g. rm of a busy file); write files with the Write tool.
- API dependency order: auth.current_parent, consent.require_consent, then api.get_rt (holds the lock).

## Running / not committed
- Services running: dev servers (preview "homenet-dev") may be running   ·   Not committed: none
