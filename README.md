# HomeNet Guardian

A home-network dashboard for parents that needs **nothing installed on the child's device**. It works only from network data: which site names devices ask for, when, and how much. It never reads content.

> **Status: in progress.** This is a showcase project and runs on a **simulated** family network (no real router). The dashboard, screenshots, an animated demo and a "how it works" diagram are coming as the plan progresses.

## What it will do
- **Devices:** who is on the network, online/offline, assigned to each child with an age profile.
- **Live activity:** a Wireshark-style table of site requests with allowed/blocked decisions.
- **Rules:** explicit sites blocked by default, category blocks, internet schedules, one-click pause.
- **Payments & stores:** store and payment sites need a parent's approval (for example, 30 minutes).
- **Where time goes:** estimated time per category and site, by time of day.
- **Weekly and monthly reports.**
- **Honesty:** the parent confirms they told the child, and a page explains what this tool can NOT see (message content, mobile data, VPNs, encrypted DNS).

## Run it (development)
```
npm run setup
npm run dev
```
Then open http://127.0.0.1:5173. It runs only on your own computer.

## Licence
MIT, see [LICENSE](LICENSE).
