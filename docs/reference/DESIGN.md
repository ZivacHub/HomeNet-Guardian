# Design
Read when: doing any UI work on the dashboard. Decisions: D7 (light + dark), D22 (clean product, blue, top navigation), D23 (explicit names hidden), D24 (icons, bundled fonts, phone width, small motion).

## Direction
- Clean product look in blue, like a modern router or banking app: familiar, trustworthy, quiet. Mode: Operate (parents complete tasks); familiarity is a feature.
- One memorable element only: the Overview's "At home right now" strip (each family member as a row, their devices lit like router LEDs). Everything else stays disciplined.
- Avoid: walls of identical rounded cards, nested cards, big-number hero tiles, eyebrow labels above headings, ALL-CAPS labels, gradient text, coloured side-borders on alerts, emoji as icons, decorative motion, monospace as decoration.

## Tokens (dashboard/src/styles/tokens.css; never hard-code colours)
| Token | Light | Dark | Use |
|---|---|---|---|
| --bg | #f6f8fb | #0d1522 | page |
| --surface | #ffffff | #131d2e | panels, tables |
| --surface-2 | #eef2f8 | #18243a | second layer: table heads, tabs, pills |
| --line / --line-strong | #e1e7ef / #c9d3e0 | #22304a / #2f4060 | borders |
| --ink / --ink-2 / --muted | #0f1b2d / #3b4a60 / #5b6b82 | #e6ecf5 / #c3cede / #93a2b8 | text |
| --accent | #2457d6 | #7a9bff | primary actions, current nav, links, info only |
| --ok / --block / --warn | #1f8a5b / #c8372d / #9a6414 | #4cc38a / #ff7a6e / #e7b15a | allowed / blocked / warning, each with a -soft background |

## Type
- IBM Plex Sans (400/500/600/700) for everything; IBM Plex Mono only for real network data: domains, MAC/IP addresses, timestamps in tables. Fonts are bundled (@fontsource, OFL); no outside requests.
- Fixed rem scale: 12 / 13 / 15 (body) / 17 / 22 (page title) / 28. Sentence case everywhere. Numbers in tables use `.num` (tabular).

## Layout
- Sticky top bar (brand, 8 nav links, "Simulated network" pill with day and time, theme switch, parent, log out). Content `.page`, left-aligned, max 1200 px, 32 px top padding.
- Page head: h1 + one-line plain description (`.page-head`). Then content in `.panel` blocks; tables sit inside one panel, not in cards per row.
- Phone (< 640 px): nav scrolls sideways under the brand; grids collapse to one column; tables scroll inside their panel.

## Components (dashboard/src/styles/ui.css) — reuse, do not restyle
- Buttons: `.btn` + `.btn-primary | .btn-secondary | .btn-danger | .btn-ghost`, sizes `.btn-lg`, `.btn-icon`. Labels name the action ("Approve 30 min", "Pause internet").
- Fields: `.field` > label + `.input` / `.select`; `.check` for checkboxes.
- Status: `.badge-ok` (Allowed), `.badge-block` (Blocked), `.badge-warn`, `.badge-info`, `.badge-plain`.
- Notes: `.callout-info | -warn | -error` with a lucide icon. Tables: `.table-wrap` > `.table`. Empty state `.empty` (teaches what to do). Loading `.skeleton`, not spinners.
- Icons: lucide-react only, 16 px in buttons, 18 px in callouts.
- Explicit domains (category `explicit`) are shown as "Explicit site (hidden)" with a "Show" button (D23); never in screenshots.
- Every time number says "estimate" (or "about") with the note from /api/meta.

## Motion
- 150-250 ms, ease-out (`--ease-out`). Only for state: new live rows slide/fade in, approve/deny feedback, nav underline. Respect prefers-reduced-motion (base.css).

## Verification
- playwright/browser screenshots at 1280 and 390 wide, light and dark; no console errors except expected 401 before login; run `impeccable detect --json dashboard/src`.
