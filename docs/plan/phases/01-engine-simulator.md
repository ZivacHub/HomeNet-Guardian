# Phase 1 — Engine + simulator
Board: docs/plan/BOARD.md lists this phase's steps and ticks. This file holds the detail.

## Purpose in plain words
The "brain": a pretend family network and the rules that decide what is allowed. At the end you run one command and read, in plain text, a family's day: which devices went online, which sites they asked for, what got blocked, the payment request, night use and the warnings. Tests prove the rules work.

## Read first (when working on this phase)
- docs/PRODUCT.md; IDEA.md sections 2-4 (what it sees and does not see)

## Steps
**1.1 Data model and SQLite tables** — Grade: strong (data model; everything builds on it). Done when: tables for devices (name, owner/child, type, MAC, last seen), children + age profile (8/13/16), queries (time, device, domain, source DNS/SNI, bytes, category, decision + reason), rules, schedules, approval requests, alerts, parents, settings. Test: pytest creates an empty database and writes/reads one row per table.
**1.2 Data source "adapter" + simulator** — Grade: strong (the plug-in shape OpenWrt must fit later). Done when: one interface (devices(), queries(since)) with a SimulatorAdapter that makes a family day from a fixed random seed (same result every run): 2 parents, 2 kids (ages 9 and 14), ~8 devices, a few thousand DNS queries spread realistically over the day, with these events: explicit site tried, night use (after 23:00), payment attempt, new unknown device, a device that stops using our DNS (possible bypass). An OpenWrtAdapter stub documents which router logs it would read. Test: pytest: same seed gives the same output; every event type appears.
**1.3 Site categories** — Grade: standard (data file + lookup). Done when: own category list (~200 well-known domains: social, video, games, learning, shopping/payments, other) + StevenBlack porn list (MIT, licence kept) as "explicit"; subdomains match their parent (m.youtube.com = video). Test: pytest on 20 sample domains.
**1.4 Rules engine: block, categories, schedule, pause** — Grade: strong (core logic, many edge cases). Done when: each query gets allowed/blocked with a reason; explicit blocked by default; category blocks per child; schedules (e.g. school nights 22:00-07:00); one-click pause per child or whole home; age-profile defaults. Test: pytest table of cases (time, child, domain = expected decision + reason).
**1.5 Payments as approval requests** — Grade: strong (money-related logic, even simulated). Done when: store/payment domains blocked by default; an attempt creates a request; the parent approves for N minutes (e.g. 30) or denies; after the time it blocks again; every decision logged. App text: "domain-level only; real purchase control lives in the phone's family settings". Test: pytest: attempt, request, approve, allowed for 30 min, blocked at minute 31.
**1.6 Alerts** — Grade: standard (clear rules). Done when: alerts for new device, explicit site blocked, night use, approval waiting, possible DNS bypass (device has traffic but no DNS queries for X minutes). Test: pytest on the simulated day: each alert appears once at the expected time.
**1.7 Time-spent estimate** — Grade: standard (known approach). Done when: minutes per category/site per child from query bursts (a gap over 5 min ends a session); always labelled "estimate". Test: pytest on a hand-made sequence with a known answer.
**1.8 "Day in the life" script + all tests** — Grade: light (runs what exists). Done when: `python -m homenet.demo` prints a readable timeline and summary. Test: run it; all pytest tests pass; output saved to docs/proof/day-in-the-life.txt.

## Risks and open points (only for this phase)
- StevenBlack list is large (100k+ lines): bundle compressed or download at setup; decided in 1.3 by size.

## Phase gate record
- (filled at the gate)
