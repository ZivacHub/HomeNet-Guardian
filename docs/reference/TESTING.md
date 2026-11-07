# Testing

## Commands
- Unit + API: `cd backend && .venv/Scripts/python -m pytest`
- Demo day (Phase 1): `python -m homenet.demo`
- E2E/visual: playwright-cli screenshots of the running dashboard

## What "verified" means
- Logic: tests pass, new behavior has a test.
- UI: screenshots in light and dark at desktop (1280) and phone (375), no console errors.
- API: success + not-logged-in + bad-input cases.
- Security: Claude's review + local probing (Phase 5); fix or document every finding.
