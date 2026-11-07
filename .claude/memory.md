# Project memory
Append newest entries at the bottom. Format: `YYYY-MM-DD: what changed / why / paths`.


2026-11-07: /new-project done; plan v1 approved (7 phases, 34 steps). Docs in docs/, decisions D1-D13. Phase 0 started: CLAUDE.md, INDEX, reference files from template v4.
2026-11-07: Phase 0 done. Skeleton backend (FastAPI /api/health) + dashboard (React/Vite) start with `npm run dev`; public repo https://github.com/ZivacHub/HomeNet-Guardian (first commit dac1420). D14 Gmail on commits, D15 IDEA.md local only + neutral job wording. Lesson: npm scripts on Windows need backslash venv paths (cmd.exe).
2026-11-07: Phase 1 steps 1.1-1.5 done: db.py (11 tables), adapters (simulator family day, OpenWrt parsers tested on sample lines), categories (helper; 76,344 MIT explicit domains bundled), engine.py rules + payment approvals (32 tests). alerts.py is a stub for 1.6. Usage limit hit while the 1.7 helper was running.
2026-11-07: Phase 1 closed. alerts.py (helper, checked), demo.py (seed_family, run_day, report; python -m homenet.demo), proof in docs/proof/day-in-the-life.txt; 109 tests pass.
2026-11-07: Phase 2 closed. api.py/runtime.py/schemas.py (helper, checked): API over the engine + simulation clock on the PC clock (D19). auth.py: Argon2 (pwdlib), HttpOnly SameSite=Strict session cookie, 8 h idle, 5-fail lock, max 2 parents. consent.py (helper): consent gate + family notice + does-not-see list. retention.py: 30-day clean-up hourly on sim clock, delete-all with DELETE. Real server probed: 401/403/200 flow, binds 127.0.0.1 only. Lesson: FastAPI 0.162 nests included routers; list routes via app.openapi().
