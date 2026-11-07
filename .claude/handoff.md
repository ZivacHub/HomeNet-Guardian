# Handoff: HomeNet Guardian (folder Family_WiFi)   (updated 2026-11-07 12:00)
Git: none yet (the folder sits inside the BUSNUS workshop repo; own repo is step 0.3) · pushed: no · uncommitted: all new docs

## Where we are in the plan
Phase 0 of 7 — Foundation. Steps done 0/34. Next per plan: 0.1 Project files from template, CLAUDE.md filled. Plan Status: DRAFT, waiting for Ivan's approval.

## What we're building
A parent's dashboard for the home network that needs nothing on the child's device, running on a simulated family day, shown on a public GitHub page with screenshots, a GIF and a diagram. Goal in Ivan's words: docs/PRODUCT.md (CONFIRMED 2026-11-07).

## Last session
- Did: /new-project interview from IDEA.md + 12 choice-card answers (docs/DECISIONS.md D1-D13)
- Did: docs/PRODUCT.md confirmed; prior-art + skills search in docs/reference/PRIOR_ART.md
- Did: plan written: docs/plan/BOARD.md + docs/plan/phases/00-06 (34 steps, graded 6 light / 17 standard / 11 strong)
- Left unfinished: plan approval (Phase F of new-project); nothing built, no git

## Next steps (strictly in order; step 1 is where the next session starts)
1. Ivan approves the plan — done when: BOARD.md says `Status: APPROVED <date>` with his words in the Change log
   Read first: docs/plan/BOARD.md, docs/DECISIONS.md
2. 0.1 Project files from template, CLAUDE.md filled — done when: pickup-context runs without missing-file warnings
   Read first: docs/plan/phases/00-foundation.md, docs/DECISIONS.md
3. Phase 0 gate, then 0.2-0.4 (scaffold, own git repo, public GitHub repo ZivacHub/HomeNet-Guardian)
   Read first: docs/plan/phases/00-foundation.md

## Waiting on the owner
- Plan approval (docs/plan/BOARD.md) — yes, or changes to steps or grades

## Gotchas a fresh session would get wrong (max 8, only things still true)
- Project name is HomeNet Guardian (D5), but the folder stays Family_WiFi (D11). IDEA.md still says "Family WiFi".
- Repo is PUBLIC from the start (D2), unlike the usual private default. Scan for private data before every push.
- No Claude co-author line in any commit (D4).
- Simulator only: no PCAP import and no OpenWrt VM (D9). OpenWrt is only described in the README.
- Full 2-day plan, no rush for an outside date (D1).
- IDEA.md stays local (git-ignored) and the public files use neutral words for the job context (D15).

## Running / not committed
- Services running: none   ·   Not committed: docs/*, .claude/handoff.md (no repo yet)
