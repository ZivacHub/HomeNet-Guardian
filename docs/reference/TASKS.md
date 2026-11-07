# Tasks and workstreams

Each workstream can be run by its own agent. OWNS sets must not overlap. Gates use unlazy format.
This file also holds the work split ("parallel agent plan") and the quality checklist; docs/plan/BOARD.md only tracks progress.

## W0 Foundation
DEPENDS: none
OWNS: package manifest, config, schema, design tokens
- [ ] G0.1: project builds/starts
  CHECK: 
  EXPECT: 

## W1 Backend / API
DEPENDS: W0
OWNS: 
- [ ] G1.1: 
  CHECK: 
  EXPECT: 

## W2 UI
DEPENDS: W0
OWNS: 
- [ ] G2.1: screens render at 375/768/1280 with no console errors
  CHECK: 
  EXPECT: 

## W3 Tests / CI
DEPENDS: W0
OWNS: tests/, CI config

## W4 Security
DEPENDS: W1, W2
OWNS: security fixes (coordinate with owner workstream)
- [ ] G4.1: Strix scan has no open high/critical findings
  CHECK: strix-scan <target> quick
  EXPECT: 

## Quality checklist (every line needs an owner)
| Area | Owner | Status |
|---|---|---|
| Design (DESIGN.md followed) | W2 | |
| Accessibility | W2 | |
| Responsive / mobile | W2 | |
| Testing | W3 | |
| Security (Strix before deploy) | W4 | |
| Performance | | |
| Scalability (ARCHITECTURE.md plan) | W1 | |
| Error handling / logging | W1 | |
| Analytics / learning loop | | |
| Docs + memory.md updated | all | |
