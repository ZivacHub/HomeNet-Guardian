# Phase 6 — Showcase on GitHub
Board: docs/plan/BOARD.md lists this phase's steps and ticks. This file holds the detail.

## Purpose in plain words
The GitHub page that explains the project: what it is, a picture of how it works, a screenshot of every screen with a short explanation, a moving GIF, how it would plug into a real OpenWrt router, and what it cannot see. At the end you can send the link to the firm.

## Read first (when working on this phase)
- docs/PRODUCT.md; README.md; docs/proof/

## Steps
**6.1 How-it-works diagram** — Grade: standard. Done when: Mermaid diagram in the README: devices, then the router (DHCP gives addresses, DNS answers site names, firewall blocks), then the adapter (simulator now / OpenWrt later), rules engine, database, dashboard. Test: renders on the GitHub page.
**6.2 Screenshots of every screen** — Grade: light (scripted capture). Use: playwright-cli. Done when: docs/screenshots/*.png for all screens (light, plus a few dark) from the simulated day. Test: files exist and were looked at before use.
**6.3 Animated GIF** — Grade: standard. Use: playwright video + ffmpeg. Done when: a 10-20 s GIF (under ~8 MB): a blocked explicit site appears live, an alert shows, a payment request gets approved. Test: plays on the GitHub page.
**6.4 README text** — Grade: strong (showcase text Ivan approves; every claim must be true). Done when: what it is, why (no app on the child's device), the diagram, each screen with screenshot + 2-3 lines, how to run (one command, demo/demo), how the OpenWrt adapter would connect (dnsmasq query log, DHCP leases, firewall rules, sending all DNS to the router and blocking known encrypted-DNS servers), what it does NOT see, honest status ("showcase, not production"), credits (StevenBlack, MIT), licence. Test: Ivan's OK in chat.
**6.5 Private-data scan, push, check the page** — Grade: light (fixed procedure). Done when: file list read and scanned for keys/e-mails/personal data; pushed; GitHub page checked in the browser, also at phone size. Test: screenshot of the live GitHub page.

## Risks and open points (only for this phase)
- ffmpeg may not be installed; checked at the gate (installing needs Ivan's OK).

## Phase gate record
- Preview given in chat 2026-11-07. Tools: playwright-cli for screenshots/frames, Mermaid for the diagram (GitHub renders it), GIF built from frames (no ffmpeg on this PC; Pillow in a throwaway venv). Decisions: D26 (picture run), D27 (README review after). Ivan's go: 2026-11-07, "Continue and dont forget to update git and add some picures, try to finish this now" (D27).

## Proof (Phase 6 close, 2026-11-07)
- Picture run (D26): separate DB + set clock (Thursday 2026-11-05 23:45) via HOMENET_DB / HOMENET_CLOCK_START / HOMENET_CLOCK_SPEED and HG_API; launch configs pictures-api, pictures-web, gif-api.
- 14 screenshots in docs/screenshots (playwright-cli), demo.gif 446 KB (26 frames, clock 21:11:30 at 6x: explicit site blocked live, then the parent's warning). Payment approval is not in the GIF (it happens at 17:04; shown in payments.png instead).
- Scan before push: no .db, IDEA.md, env or browser files; no keys/e-mails in text. Live page checked: 15/15 images load, Mermaid diagram renders, GIF 960x608. Topics added. README review by Ivan after upload (D27).
