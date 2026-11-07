# Phase 5 — Security check
Board: docs/plan/BOARD.md lists this phase's steps and ticks. This file holds the detail.

## Purpose in plain words
A tool for parents must not be easy to break into. At the end there is a short list of what was tried against the app on your PC, what was found and how it was fixed. That list is good material for a security-minded firm.

## Read first (when working on this phase)
- docs/reference/SECURITY_CHECKLIST.md

## Steps
**5.1 Code security review + fixes** — Grade: strong (security). Use: /security-review. Done when: every finding fixed or written down with a reason. Test: re-run the review; findings listed in docs/reference/SECURITY_CHECKLIST.md.
**5.2 Attack the running app on localhost + fixes** — Grade: strong (security). Use: curl, playwright-cli. Done when: tried: login bypass, using the API without a session, injection in filters, script injection in device names, oversized input, access from another machine (must be refused); each with the request that proves it and the fix. Test: re-probe after the fixes.

## Risks and open points (only for this phase)
- Strix is optional (paid key); the free path above is the default.

## Phase gate record
- Preview given in chat 2026-11-07. Tools: security-review skill + own review, curl probes on 127.0.0.1 (free path; Strix needs a paid key, not used). Decisions: none new. Ivan's go: 2026-11-07, "Continue and dont forget to update git and add some picures, try to finish this now" (D27).
