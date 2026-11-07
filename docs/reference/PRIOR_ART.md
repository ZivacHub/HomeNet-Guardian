# Prior art and skills search (2026-11-07)
Read when: choosing what to borrow, picking blocklists, or explaining "how is this different" on the GitHub page.
Status: DRAFT, nothing adopted until Ivan picks (see DECISIONS.md).

## Similar projects (checked on GitHub 2026-11-07)
| Project | Stars | Licence | What it does | Worth borrowing (ideas only, no code) |
|---|---|---|---|---|
| pi-hole/pi-hole | 61.7k | EUPL-1.2 (GitHub shows NOASSERTION) | Network-wide DNS blocker with a query log and web admin | The live "query log" table: time, client, domain, status. That's our Live activity screen |
| AdguardTeam/AdGuardHome | 38.2k | GPL-3.0 | DNS blocker with per-device settings and "blocked services" | Per-device rules; one-click service toggles (e.g. "block TikTok"); a schedule for blocked services |
| StevenBlack/hosts | 31.4k | MIT | Merged blocklists with optional porn/social/gambling add-ons | A usable explicit-site list under MIT (we may include it with its licence note) |
| hagezi/dns-blocklists | 28.3k | GPL-3.0 | Large curated DNS blocklists | Reference only. GPL is too strict to bundle in an MIT repo |
| UT1 Toulouse blacklists (olbat/ut1-blacklists mirror) | 185 | CC BY-SA 4.0 per the university site (the mirror shows none) | Sites sorted by category (social, games, shopping...) | Category names. Bundling data would need credit + share-alike, so the default is not to bundle |

**Our edge:** one parent-friendly dashboard on top of a pluggable data source (a simulator now, an OpenWrt router later), payments as parent approvals, weekly/monthly reports, and an honest "what this does NOT see" page. Pi-hole and AdGuard are ad blockers for admins and don't cover any of that.

## Skills search (`npx skills find`, 2026-11-07)
Searched: "parental control dashboard", "fastapi", "react dashboard". Found: nextdns-api (1 install, for a paid DNS service we don't use), api-docs generators, a React admin template skill (71 installs), a UX audit skill. **Verdict: nothing worth adopting.** The installed design skills (D10) plus playwright-cli for screenshots already cover the needs.

## Versions checked (2026-11-07)
Python 3.11.9 and Node 24.13.1 on this PC. Latest: FastAPI 0.162.0, React 19.3.1, Vite 8.3.6, Recharts 3.10.1. Re-check with context7 before installing.
