# Phase 3 — Dashboard screens
Board: docs/plan/BOARD.md lists this phase's steps and ticks. This file holds the detail.

## Purpose in plain words
The part you and the firm look at: 8 screens in English, with a calm light theme and a dark one. At the end you click through the whole simulated family day, with a screenshot of every screen.

## Read first (when working on this phase)
- docs/reference/DESIGN.md (filled in 3.1); CLAUDE.md "Design stack"

## Steps
Every screen: built with frontend-design + impeccable, checked with design-taste-frontend, and screenshotted in light AND dark with playwright-cli before ticking.
**3.1 App shell, top navigation (D22), light/dark themes** — Grade: strong (sets the whole look; design judgement). Done when: side navigation, login screen, theme switch remembered; DESIGN.md records colours, fonts, spacing. Test: screenshots light + dark.
**3.2 Overview** — Grade: standard. Done when: who is online now, today's activity per child, alerts (new device, blocked explicit, night use, approvals waiting, possible bypass) with one-click actions. Test: screenshots; numbers match the API.
**3.3 Devices** — Grade: standard. Done when: list (name, owner, type, last seen, online/offline), assign to child, age profile per child, rename an unknown device. Test: screenshot; assigning a device changes its rules in the API.
**3.4 Live activity (Wireshark-style)** — Grade: standard. Done when: table time / device / site / category / allowed-blocked + reason, filters, new rows appear while the simulator plays. Test: screenshot; filter by device works.
**3.5 Where time goes** — Grade: standard. Use: Recharts, dataviz skill. Done when: per child: category split, top sites, time-of-day chart, every number marked "estimate". Test: screenshot.
**3.6 Rules** — Grade: standard. Done when: category toggles per child, explicit blocked by default, schedule editor, big "Pause internet" button. Test: toggling a rule changes the next decision in Live activity.
**3.7 Payments & stores** — Grade: standard. Done when: pending requests with Approve 30 min / Deny, decision log, the honest note about phone family settings. Test: approve, then the device's payment query shows allowed.
**3.8 Settings & "What this does NOT see"** — Grade: standard (text from IDEA.md section 4). Done when: retention setting, delete everything, parents, notice template, and the limits page (content, mobile data, VPN, encrypted DNS, ECH, random device addresses). Test: screenshot.
**3.9 Design review and polish** — Grade: strong (judgement). Use: impeccable critique, emil-design-eng, review-animations. Done when: review findings fixed; small transitions for live rows and approvals. Test: before/after screenshots.

## Risks and open points (only for this phase)
- Biggest phase; if time runs short, Ivan is asked what to cut (3.9 polish would be my proposal).

## Phase gate record
- Plain-words preview shown: 2026-11-07. Repos: GitHub "parental control dashboard" (5 repos, 0-1 stars; techguard MIT Pi-hole add-on: nothing to borrow), "network monitoring dashboard react" (3 repos, 0 stars). Skills: design stack already chosen (D10). Libraries: Recharts 3.10.1, lucide-react 1.70.0. Decisions asked: D22-D24. Ivan's go: 2026-11-07, "Go, start Phase 3".
