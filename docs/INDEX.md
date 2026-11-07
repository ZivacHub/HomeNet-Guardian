# Docs index
Every file in docs/ is listed here with WHEN to read it. A script checks that none is missing. If you are a Claude instance that just landed in this project: read the "Always" rows, then only what the next step needs.

## Always (start of every session; the start-up check and pickup load these)
| File | What it is |
|---|---|
| ../CLAUDE.md | Rules, commands, stack, skills for this project (short). |
| PRODUCT.md | The goal in Ivan's own words. The compass. |
| plan/BOARD.md | Status board: what is done, what is next, and the change log. |
| DECISIONS.md | What Ivan decided; the open and proposed ones are at the top. |
| ../.claude/handoff.md | Where the last session stopped, numbered next steps, and the `Read first:` line. |

## For the current phase only
| File | Read when |
|---|---|
| plan/phases/00-foundation.md | Working on Phase 0 (setup, git, GitHub). |
| plan/phases/01-engine-simulator.md | Working on Phase 1 (data model, simulator, rules, alerts). |
| plan/phases/02-server-login.md | Working on Phase 2 (local API, login, consent, cleanup). |
| plan/phases/03-dashboard-screens.md | Working on Phase 3 (the 8 screens, themes). |
| plan/phases/04-reports.md | Working on Phase 4 (weekly/monthly reports, export). |
| plan/phases/05-security.md | Working on Phase 5 (security review and probing). |
| plan/phases/06-showcase.md | Working on Phase 6 (diagram, screenshots, GIF, README, push). |

## On demand (read only when the step touches it)
| File | Read when |
|---|---|
| reference/ARCHITECTURE.md | Changing the stack, data model, adapter interface or security design. |
| reference/DESIGN.md | Doing any UI work. |
| reference/TESTING.md | Writing or running tests, or deciding what "verified" means. |
| reference/TASKS.md | Splitting work between parallel agents; quality checklist. |
| reference/SECURITY_CHECKLIST.md | Phase 2 login work and Phase 5. |
| reference/PRIOR_ART.md | Similar projects, blocklist licences, "how is this different" text. |
| ../IDEA.md | Ivan's original idea note (local only, not in git). What the app sees and does not see, screen list. |
| ../.claude/memory.md | Digging into recent history (current month). |

## Rules for this folder
- New doc? Put it in the right place (goal/decisions/plan at the top, background in reference/) and add a row here in the same change.
- Keep the "Always" files small. If one grows past about 8 KB, split it.
- The root of the project holds only CLAUDE.md, README.md, IDEA.md and the code.
