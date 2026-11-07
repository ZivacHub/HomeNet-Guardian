# Security checklist (before you share a link or deploy)
From the owner's saved list "19 things to check" (2026-10-15). Run it in the security phase and before any public launch. Tick each item with proof (a test, a probe, a screenshot) or write "N/A: <why>". Claude's own review + local probing is the free way to check them (global CLAUDE.md "Security").

1. [ ] Protect admin routes (only the right people can open admin pages and admin API calls)
2. [ ] Server-side access checks (the server decides who may see what, not the browser)
3. [ ] Row-level security (database rules so one user can't read another's rows)
4. [ ] Verify email (sign-ups are confirmed before access)
5. [ ] Hash passwords (never store them as plain text)
6. [ ] No local auth tokens (don't keep login secrets where page scripts can read them)
7. [ ] Server-side secrets (API keys live on the server only)
8. [ ] Keep .env off GitHub (ignored, and checked in the git history too)
9. [ ] No secrets in logs
10. [ ] Parameterized SQL (no string-built queries)
11. [ ] Validate form inputs (server side)
12. [ ] Block XSS (escape or sanitize anything shown back to a page)
13. [ ] Validate uploads (type, size, name, where it is stored)
14. [ ] Verify webhooks (signature checked before acting)
15. [ ] Rate-limit requests (login, sign-up, expensive calls)
16. [ ] Tighten CORS (only the origins that need it)
17. [ ] Production debug off
18. [ ] Patch dependencies (known-vulnerability check)
19. [ ] Claude security scan (`/security-review` + probing the running app)
