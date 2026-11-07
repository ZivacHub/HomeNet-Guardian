"""A made-up family network: Mom, Dad, Ana (14) and Luka (9) on one home Wi-Fi.

The simulator plays the role of the router. It produces the same kind of data a real
router logs (device leases and site-name lookups) for one or more days. A fixed seed makes
every run identical, so tests and screenshots are repeatable.

Besides ordinary browsing it scripts the moments a parent cares about:
  * Ana tries an explicit site (21:14)
  * Luka tries an in-app purchase (17:04) and tries again after a parent approves
  * Luka picks up his tablet after his bedtime (20:45)
  * Ana is on her phone after 23:00 on a school night
  * an unknown phone joins the Wi-Fi (16:20)
  * Ana's laptop switches to encrypted DNS (19:30): its lookups vanish from the router log
    while its connections continue, the classic sign of a filter bypass
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from typing import Iterator

from .base import DeviceSeen, NetEvent

# --- the family -------------------------------------------------------------------------

FAMILY_CHILDREN = [
    {"name": "Ana", "age": 14, "age_profile": 13},
    {"name": "Luka", "age": 9, "age_profile": 8},
]

FAMILY_PARENTS = ["Mom", "Dad"]


@dataclass(frozen=True)
class SimDevice:
    mac: str
    hostname: str
    ip: str
    kind: str
    owner: str            # "Mom", "Dad", "Ana", "Luka", "Family" or "" (unknown)
    display_name: str
    known: bool = True


DEVICES = [
    SimDevice("3c:22:fb:10:00:01", "Moms-iPhone", "192.168.1.21", "phone", "Mom", "Mom's iPhone"),
    SimDevice("58:24:29:10:00:02", "Dads-Pixel", "192.168.1.22", "phone", "Dad", "Dad's Pixel"),
    SimDevice("f4:8c:50:10:00:03", "DAD-LAPTOP", "192.168.1.23", "laptop", "Dad", "Dad's laptop"),
    SimDevice("a8:9c:ed:10:00:04", "Anas-Galaxy-S23", "192.168.1.31", "phone", "Ana", "Ana's phone"),
    SimDevice("e0:d5:5e:10:00:05", "ana-laptop", "192.168.1.32", "laptop", "Ana", "Ana's laptop"),
    SimDevice("d0:81:7a:10:00:06", "Lukas-iPad", "192.168.1.41", "tablet", "Luka", "Luka's iPad"),
    SimDevice("00:a0:de:10:00:07", "LivingRoom-TV", "192.168.1.50", "tv", "Family", "Living room TV"),
    SimDevice("bc:60:a7:10:00:08", "PS5-Luka", "192.168.1.42", "console", "Luka", "Luka's PlayStation"),
]
# A visitor's phone. Its MAC starts with "da": the "locally administered" bit is set, which is
# what Android/iOS private (randomised) addresses look like.
UNKNOWN_DEVICE = SimDevice("da:4f:91:3e:7c:09", "Galaxy-A14", "192.168.1.77", "phone", "",
                           "Galaxy-A14", known=False)
UNKNOWN_JOINS = time(16, 20)
UNKNOWN_LEAVES = time(18, 5)

EXPLICIT_TRY_DOMAIN = "redtube.com"          # present in the bundled explicit list
UNLISTED_DOH = "doh.private-resolver.net"    # an encrypted-DNS server NOT on our block list

# --- what each site looks like on the wire -----------------------------------------------
# main domain plus the helper domains an app or page loads alongside it

SITES: dict[str, list[str]] = {
    "youtube":   ["www.youtube.com", "i.ytimg.com", "rr3---sn-hpa7zn7s.googlevideo.com", "yt3.ggpht.com"],
    "tiktok":    ["www.tiktok.com", "v16m.tiktokcdn.com", "p16-sign.tiktokcdn-us.com"],
    "instagram": ["www.instagram.com", "scontent.cdninstagram.com", "graph.instagram.com"],
    "snapchat":  ["app.snapchat.com", "cf-st.sc-cdn.net"],
    "whatsapp":  ["g.whatsapp.net", "mmg.whatsapp.net"],
    "discord":   ["discord.com", "gateway.discord.gg", "cdn.discordapp.com"],
    "netflix":   ["www.netflix.com", "ipv4-c001-zag001-ix.1.oca.nflxvideo.net"],
    "spotify":   ["open.spotify.com", "i.scdn.co", "audio-ak-spotify-com.akamaized.net"],
    "roblox":    ["www.roblox.com", "apis.roblox.com", "t3.rbxcdn.com"],
    "minecraft": ["minecraft.net", "session.minecraft.net"],
    "fortnite":  ["fortnite.com", "account-public-service-prod.ol.epicgames.com"],
    "brawl":     ["game.brawlstarsgame.com", "supercell.com"],
    "psn":       ["store.playstation.com", "np.playstation.net"],
    "wikipedia": ["en.wikipedia.org", "upload.wikimedia.org"],
    "khan":      ["www.khanacademy.org", "cdn.kastatic.org"],
    "duolingo":  ["www.duolingo.com", "d35aaqx5ub95lt.cloudfront.net"],
    "classroom": ["classroom.google.com", "docs.google.com"],
    "ednevnik":  ["ocjene.skole.hr", "e-dnevnik.skole.hr"],
    "google":    ["www.google.com", "www.gstatic.com"],
    "news":      ["www.index.hr", "www.bbc.com"],
    "shopping":  ["www.amazon.com", "www.njuskalo.hr"],
    "mail":      ["mail.google.com", "outlook.office.com"],
    "teams":     ["teams.microsoft.com", "statics.teams.cdn.office.net"],
    "linkedin":  ["www.linkedin.com", "static.licdn.com"],
    "facebook":  ["www.facebook.com", "static.xx.fbcdn.net"],
    "reddit":    ["www.reddit.com", "i.redd.it"],
}

# background chatter every device makes (time sync, connectivity checks, updates)
SYSTEM_DOMAINS = {
    "phone": ["connectivitycheck.gstatic.com", "time.android.com", "clients3.google.com", "captive.apple.com"],
    "tablet": ["captive.apple.com", "time.apple.com", "gateway.icloud.com"],
    "laptop": ["www.msftconnecttest.com", "time.windows.com", "settings-win.data.microsoft.com"],
    "tv": ["time.samsungcloud.com", "connectivitycheck.gstatic.com"],
    "console": ["np.playstation.net", "time.playstation.net"],
}

# (window start, window end, {site: weight}) — when a device is used and for what
Window = tuple[time, time, dict[str, int]]

USAGE: dict[str, list[Window]] = {
    "Moms-iPhone": [
        (time(6, 40), time(7, 30), {"news": 3, "whatsapp": 3, "mail": 2}),
        (time(12, 0), time(12, 40), {"whatsapp": 3, "instagram": 2, "shopping": 1}),
        (time(19, 0), time(22, 30), {"instagram": 3, "facebook": 2, "whatsapp": 3, "netflix": 1}),
    ],
    "Dads-Pixel": [
        (time(6, 30), time(7, 15), {"news": 3, "whatsapp": 2}),
        (time(17, 30), time(18, 30), {"youtube": 2, "reddit": 2, "whatsapp": 2}),
        (time(21, 0), time(23, 30), {"youtube": 3, "reddit": 2, "news": 1}),
    ],
    "DAD-LAPTOP": [
        (time(8, 0), time(16, 0), {"mail": 3, "teams": 4, "google": 2, "linkedin": 1}),
    ],
    "Anas-Galaxy-S23": [
        (time(6, 50), time(7, 30), {"instagram": 3, "snapchat": 3, "spotify": 2}),
        (time(14, 30), time(15, 30), {"tiktok": 4, "snapchat": 3, "instagram": 2}),
        (time(17, 0), time(19, 0), {"tiktok": 4, "instagram": 3, "discord": 2, "spotify": 1}),
        (time(20, 0), time(22, 0), {"tiktok": 4, "instagram": 3, "snapchat": 2, "youtube": 2}),
    ],
    "ana-laptop": [
        (time(15, 30), time(17, 0), {"classroom": 4, "wikipedia": 3, "khan": 2, "ednevnik": 1, "google": 2}),
        (time(19, 30), time(21, 0), {"youtube": 4, "discord": 2, "netflix": 1}),
    ],
    "Lukas-iPad": [
        (time(14, 0), time(15, 0), {"duolingo": 2, "khan": 2, "youtube": 3}),
        (time(16, 30), time(18, 0), {"roblox": 5, "youtube": 3, "minecraft": 2}),
        (time(19, 0), time(20, 15), {"youtube": 4, "roblox": 3, "brawl": 1}),
    ],
    "LivingRoom-TV": [
        (time(18, 30), time(21, 30), {"netflix": 4, "youtube": 2}),
    ],
    "PS5-Luka": [
        (time(18, 0), time(19, 0), {"fortnite": 4, "psn": 1, "minecraft": 1}),
    ],
    "Galaxy-A14": [
        (UNKNOWN_JOINS, UNKNOWN_LEAVES, {"youtube": 3, "instagram": 3, "tiktok": 2, "roblox": 1}),
    ],
}

KIND_BY_HOST = {d.hostname: d.kind for d in DEVICES + [UNKNOWN_DEVICE]}
MAC_BY_HOST = {d.hostname: d.mac for d in DEVICES + [UNKNOWN_DEVICE]}


@dataclass
class _DayPlan:
    events: list[NetEvent] = field(default_factory=list)


def _at(day: date, t: time) -> datetime:
    return datetime.combine(day, t)


class SimulatorAdapter:
    """Pretend router for the demo family. Same seed + same dates = identical output."""

    name = "simulator"

    def __init__(self, start: date = date(2026, 11, 5), days: int = 1, seed: int = 7) -> None:
        self.start = start
        self.days = days
        self.seed = seed
        self._events: list[NetEvent] | None = None

    # --- DataSource -------------------------------------------------------------------
    def devices(self) -> list[DeviceSeen]:
        first = _at(self.start, time(0, 0))
        seen = [DeviceSeen(d.mac, d.hostname, d.ip, first, d.kind) for d in DEVICES]
        seen.append(DeviceSeen(UNKNOWN_DEVICE.mac, UNKNOWN_DEVICE.hostname, UNKNOWN_DEVICE.ip,
                               _at(self.start, UNKNOWN_JOINS), UNKNOWN_DEVICE.kind))
        return seen

    def queries(self, since: datetime | None = None,
                until: datetime | None = None) -> Iterator[NetEvent]:
        for e in self._all_events():
            if since is not None and e.ts <= since:
                continue
            if until is not None and e.ts > until:
                break
            yield e

    # --- generation -------------------------------------------------------------------
    def _all_events(self) -> list[NetEvent]:
        if self._events is None:
            events: list[NetEvent] = []
            for i in range(self.days):
                day = self.start + timedelta(days=i)
                rng = random.Random(self.seed * 10_000 + day.toordinal())
                events.extend(self._make_day(day, rng))
            events.sort(key=lambda e: (e.ts, e.mac, e.domain))
            self._events = events
        return self._events

    def _make_day(self, day: date, rng: random.Random) -> list[NetEvent]:
        out: list[NetEvent] = []
        bypass_from = _at(day, time(19, 30))
        for host, windows in USAGE.items():
            mac = MAC_BY_HOST[host]
            for start, end, mix in windows:
                out.extend(self._browse(rng, day, mac, start, end, mix,
                                        sni_only_after=bypass_from if host == "ana-laptop" else None))
            out.extend(self._background(rng, day, mac, KIND_BY_HOST[host], windows,
                                        sni_only_after=bypass_from if host == "ana-laptop" else None))
        out.extend(self._scripted(rng, day))
        return out

    def _browse(self, rng: random.Random, day: date, mac: str, start: time, end: time,
                mix: dict[str, int], sni_only_after: datetime | None) -> list[NetEvent]:
        """Sessions of 4-30 minutes inside the window, one lookup every 15-90 seconds."""
        out: list[NetEvent] = []
        t = _at(day, start) + timedelta(seconds=rng.randint(0, 240))
        stop = _at(day, end)
        sites, weights = list(mix), list(mix.values())
        while t < stop:
            site = rng.choices(sites, weights)[0]
            session_end = min(stop, t + timedelta(minutes=rng.randint(4, 30)))
            while t < session_end:
                domain = rng.choice(SITES[site])
                source = "dns"
                if sni_only_after is not None and t >= sni_only_after:
                    source = "sni"   # lookups now go encrypted; the router only sees the TLS name
                out.append(NetEvent(t, mac, domain, source, rng.randint(2_000, 900_000)))
                t += timedelta(seconds=rng.randint(15, 90))
            t += timedelta(minutes=rng.randint(1, 12))   # a short break between sessions
        return out

    def _background(self, rng: random.Random, day: date, mac: str, kind: str,
                    windows: list[Window], sni_only_after: datetime | None) -> list[NetEvent]:
        """Every 10-25 minutes while the device is on (its first window start to its last end)."""
        domains = SYSTEM_DOMAINS.get(kind, SYSTEM_DOMAINS["phone"])
        t = _at(day, min(w[0] for w in windows))
        stop = _at(day, max(w[1] for w in windows))
        out = []
        while t < stop:
            source = "sni" if sni_only_after is not None and t >= sni_only_after else "dns"
            out.append(NetEvent(t, mac, rng.choice(domains), source, rng.randint(300, 3_000)))
            t += timedelta(minutes=rng.randint(10, 25))
        return out

    def _scripted(self, rng: random.Random, day: date) -> list[NetEvent]:
        ana_phone = MAC_BY_HOST["Anas-Galaxy-S23"]
        ana_laptop = MAC_BY_HOST["ana-laptop"]
        luka = MAC_BY_HOST["Lukas-iPad"]
        ev: list[NetEvent] = []

        def add(hh: int, mm: int, ss: int, mac: str, domain: str, source: str = "dns",
                size: int = 4_000) -> None:
            ev.append(NetEvent(datetime.combine(day, time(hh, mm, ss)), mac, domain, source, size))

        # Ana tries an explicit site: the page and two retries
        add(21, 14, 5, ana_phone, EXPLICIT_TRY_DOMAIN)
        add(21, 14, 9, ana_phone, "www." + EXPLICIT_TRY_DOMAIN)
        add(21, 14, 40, ana_phone, EXPLICIT_TRY_DOMAIN)

        # Luka tries to buy Robux in the app store, waits, tries again later
        add(17, 4, 12, luka, "buy.itunes.apple.com")
        add(17, 4, 15, luka, "apps.apple.com")
        add(17, 6, 30, luka, "buy.itunes.apple.com")
        add(17, 12, 0, luka, "buy.itunes.apple.com", size=12_000)   # after a parent approves
        add(17, 12, 4, luka, "apps.apple.com")
        add(17, 41, 0, luka, "buy.itunes.apple.com")                # a second buy after 30 min

        # Luka's iPad after his bedtime (age-8 profile: no internet after 20:30)
        for i, dom in enumerate(["www.youtube.com", "i.ytimg.com", "www.youtube.com", "www.roblox.com"]):
            add(20, 45 + i * 2, 10, luka, dom)

        # Ana on her phone after 23:00 on a school night
        t = datetime.combine(day, time(23, 6))
        while t < datetime.combine(day, time(23, 38)):
            ev.append(NetEvent(t, ana_phone, rng.choice(SITES["tiktok"] + SITES["instagram"]), "dns",
                               rng.randint(20_000, 700_000)))
            t += timedelta(seconds=rng.randint(20, 75))

        # Ana's laptop turns on encrypted DNS: a known server first (blocked), then an unlisted one
        add(19, 29, 50, ana_laptop, "dns.google")
        add(19, 29, 52, ana_laptop, "cloudflare-dns.com")
        add(19, 29, 58, ana_laptop, UNLISTED_DOH)
        return ev
