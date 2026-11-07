# Decisions

Rule: a decision is **decided** only when the owner said it. Anything Claude suggested is **proposed** until the owner answers.
A vague answer ("depends", "whatever") is not a decision: write Claude's reading as `[proposed]` and ask the owner to confirm.
Never delete: replace with `[superseded by D<n>]`. Status line format (read by a script): `## D<n> — <title>   [decided <date>]` or `[open]` / `[proposed]` / `[superseded by D<n>]`.
Layout: the two sections below. When a decision is answered, move its block from "Waiting on the owner" to the bottom of "Decided" (so the top of this file is always what is still open).

## Waiting on the owner (open and proposed)

(none right now; plan approval is tracked on docs/plan/BOARD.md)

## Decided (newest at the bottom)

## D1 — Pace and deadline   [decided 2026-11-07]
**Question:** aim for an early outside date with a thin version, or the full 2-day plan?
**The owner said:** "Full 2-day plan, send later" (choice card, 2026-11-07)
**Result:** all planned screens, no rush; shared later.

## D2 — Who sees the GitHub repo   [decided 2026-11-07]
**Options:** private now/public later; public from the start; always private.
**The owner said:** "Public from the start" (2026-11-07)
**Result:** public repo from the first push. Before EVERY push: secrets/personal-data scan. Only simulated data in the repo.

## D3 — Language   [decided 2026-11-07]
**The owner said:** "English" (2026-11-07)
**Result:** dashboard and GitHub page in English.

## D4 — Claude as co-author   [decided 2026-11-07]
**The owner said:** "No, only me" (2026-11-07)
**Result:** no Co-Authored-By line; `.claude/settings.json` attribution empty.

## D5 — Name   [decided 2026-11-07]
**The owner said:** "HomeNet Guardian" (2026-11-07)
**Result:** shown at the top of the dashboard and the GitHub page.

## D6 — Users   [decided 2026-11-07]
**The owner said:** "Showcase only" (2026-11-07)
**Result:** demo on simulated data; no installer, no real-family support.

## D7 — Look   [decided 2026-11-07]
**The owner said:** "Both (light/dark switch)" (2026-11-07)
**Result:** calm light theme by default + dark theme switch.

## D8 — Showcase material on GitHub   [decided 2026-11-07]
**The owner said:** "Screenshots of each screen, Animated GIF, How-it-works diagram" (2026-11-07)
**Result:** README with one screenshot per screen + explanation, a 10-20 s GIF, a diagram devices → router → engine → dashboard. No video.

## D9 — Stack   [decided 2026-11-07]
**The owner said:** "Python + React dashboard" (2026-11-07)
**Result:** Python engine + simulator + SQLite + local web API; React dashboard as a separate app. Real traffic import: "Simulator only". OpenWrt VM: "No, describe it only".

## D10 — Design helpers   [decided 2026-11-07]
**The owner said:** "Add emil-design-eng too" (2026-11-07)
**Result:** frontend-design (base), impeccable (layout, type, themes), design-taste-frontend (anti-generic check), emil-design-eng (polish, motion). Checked with playwright-cli screenshots.

## D11 — Smaller defaults   [decided 2026-11-07]
**The owner said:** "Accept all" (2026-11-07)
**Result:** GitHub repo ZivacHub/HomeNet-Guardian (public, D2); folder stays Family_WiFi; MIT licence; demo login demo/demo documented in README (fake data, localhost only); logs kept 30 days; charts with Recharts; diagram as Mermaid so GitHub renders it; GIF recorded automatically from the browser (playwright).

## D12 — Site lists   [decided 2026-11-07]
**Options:** StevenBlack (MIT) for explicit + our own category list; or only our own list.
**The owner said:** "StevenBlack + our own list" (2026-11-07)
**Result:** explicit sites from StevenBlack hosts (MIT, credited in README/NOTICE); categories from our own ~200-site list.

## D13 — Phase list   [decided 2026-11-07]
**The owner said:** "Yes, write the steps" (2026-11-07) for: 0 Foundation, 1 Engine + simulator, 2 Server + login, 3 Dashboard screens, 4 Reports, 5 Security check, 6 Showcase.
**Result:** steps written in docs/plan/; waiting for plan approval.

## D14 — E-mail on commits in the public repo   [decided 2026-11-07]
**Options:** GitHub's private no-reply address; or the Gmail.
**The owner said:** "My Gmail" (2026-11-07)
**Result:** commits use git's normal identity Zivac <zivan9899@gmail.com>; it is visible in the public history.

## D15 — What the public repo shows   [decided 2026-11-07]
**Options:** code + plan without job notes; only code + README; everything as is.
**The owner said:** "Code + plan, no job notes" (2026-11-07)
**Result:** IDEA.md is git-ignored (stays on Ivan's PC). Tracked files use neutral words instead of the company name, application date and CV. Plan and decision log stay public.

## D16 — Where the adult-site list lives   [decided 2026-11-07]
**Options:** inside the repo compressed; or downloaded on first setup.
**The owner said:** "Inside the repo, compressed" (2026-11-07)
**Result:** only the MIT-licensed parts of StevenBlack's porn extension (Sinfonietta, Clefspeare13 pornhosts, BigDargon hostsVN; 76,345 domains, ~0.4 MB gzip) bundled in backend/homenet/data/ with a NOTICE crediting each; CC BY 4.0 parts (tiuxo, brijrajparmar27) left out. A small update command can refresh it.

## D17 — Names of the pretend family   [decided 2026-11-07]
**The owner said:** "Mom, Dad, Ana (14), Luka (9)" (2026-11-07)
**Result:** simulator family = Mom, Dad, Ana (14), Luka (9).
