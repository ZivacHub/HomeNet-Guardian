# Product: HomeNet Guardian
Status: CONFIRMED 2026-11-07 (Ivan: "Yes, that's it").  Changes here only with Ivan's OK, each with a dated line under "Changed".
This file is the compass: it is loaded at the start of every session. Keep it under 45 lines.

## The goal, in the owner's own words
> "Showcase je najbitniji." (2026-11-06) Show a networking company (mesh Wi-Fi, OpenWrt) real knowledge of Wi-Fi networks, security and management.
> "roditelji jer su svi na istome netu mogu provjeravati dijecu ... a da ne moraju instalirati neke aplikacije jer to dijeca otkriju." (2026-11-06)
> "Lets make this work, dasboard... expalin the project on git ... add a picture of dashboard and expalin how it works." (2026-11-07)

## Who it's for and what problem it solves
- A parent who wants to see what happens on the home network without installing anything on the child's device.
- Real audience now: employers reading the GitHub page (showcase only, Ivan 2026-11-07). It runs on simulated data and no real families install it.

## Non-negotiables (decisions that must not drift)
- Nothing on the child's device. It uses network data only (site names via DNS/SNI, times, amounts) and never content.
- Honesty: on first start the parent confirms they told the child, a family notice template is included, a "What this does NOT see" page exists, and estimates are labelled as estimates.
- Simulated router: a data "adapter" (a plug-in data source) feeds the engine, so a real OpenWrt adapter could replace the simulator later. The OpenWrt connection is described only and not built.
- Local only: parent login, no cloud, no outside access, logs kept for a limited time, no secrets in git.
- The GitHub page explains the project with screenshots of each screen, an animated GIF and a how-it-works diagram.
- Nothing claimed that isn't true: unfinished parts are labelled "in progress".

## What success looks like
- A public GitHub repo whose page explains how it works (diagram, screenshots, GIF) and that the firm can open and understand in 2 minutes.
- The dashboard runs with one start command and shows a simulated "day in the life of a family": devices, live activity, blocked explicit site, night use, payment request approved, new unknown device, DNS-bypass warning.
- Rule tests pass (blocking, schedule, payment approval).

## Not doing (on purpose)
- No real router, no OpenWrt virtual machine (described only).
- No real traffic recording import (PCAP), simulator only (Ivan 2026-11-07).
- No rush for an outside date: full 2-day plan, shared later (Ivan 2026-11-07).
- No installer and no support for real families.

## Changed
- 2026-11-07: drafted from IDEA.md + Ivan's interview answers.
