from datetime import date, datetime, time

from homenet.adapters import DataSource, OpenWrtAdapter, SimulatorAdapter
from homenet.adapters import simulator as sim
from homenet.adapters.openwrt import parse_leases, parse_query_log

DAY = date(2026, 11, 5)


def events(seed=7, days=1):
    return list(SimulatorAdapter(DAY, days=days, seed=seed).queries())


def test_both_adapters_fit_the_contract(tmp_path):
    assert isinstance(SimulatorAdapter(), DataSource)
    assert isinstance(OpenWrtAdapter(tmp_path / "l", tmp_path / "q", 2026), DataSource)


def test_same_seed_same_day():
    assert events(7) == events(7)
    assert events(7) != events(8)


def test_volume_and_order():
    ev = events()
    assert 2_000 <= len(ev) <= 8_000
    assert ev == sorted(ev, key=lambda e: (e.ts, e.mac, e.domain))
    assert all(e.ts.date() == DAY for e in ev)


def test_nine_devices_unknown_one_joins_later():
    devs = SimulatorAdapter(DAY).devices()
    assert len(devs) == 9
    unknown = [d for d in devs if d.mac == sim.UNKNOWN_DEVICE.mac][0]
    assert unknown.first_seen == datetime.combine(DAY, sim.UNKNOWN_JOINS)
    first_query = min(e.ts for e in events() if e.mac == unknown.mac)
    assert first_query >= unknown.first_seen


def test_every_scripted_event_is_present():
    ev = events()
    by = lambda host: [e for e in ev if e.mac == sim.MAC_BY_HOST[host]]
    ana_phone, ana_laptop, luka = by("Anas-Galaxy-S23"), by("ana-laptop"), by("Lukas-iPad")
    assert any(e.domain == sim.EXPLICIT_TRY_DOMAIN for e in ana_phone)                 # explicit try
    assert any(e.ts.time() >= time(23, 0) for e in ana_phone)                        # night use
    assert sum(e.domain == "buy.itunes.apple.com" for e in luka) >= 3                # payment tries
    assert any(time(20, 30) < e.ts.time() < time(21, 0) for e in luka)               # after bedtime
    assert any(e.domain == "dns.google" for e in ana_laptop)                         # encrypted DNS
    late = [e for e in ana_laptop if e.ts.time() >= time(19, 30)]
    assert late and all(e.source == "sni" for e in late)                             # lookups vanish


def test_since_until_filter():
    a = SimulatorAdapter(DAY)
    since, until = datetime.combine(DAY, time(17)), datetime.combine(DAY, time(18))
    part = list(a.queries(since, until))
    assert part and all(since < e.ts <= until for e in part)


def test_multi_day_has_different_days():
    ev = events(days=3)
    assert {e.ts.date() for e in ev} == {date(2026, 11, 5), date(2026, 11, 6), date(2026, 11, 7)}


# --- OpenWrt formats (sample lines in the documented format; no real router) -------------

LEASES = """1762560000 a8:9c:ed:10:00:04 192.168.1.31 Anas-Galaxy-S23 01:a8:9c:ed:10:00:04
1762560000 DA:4F:91:3E:7C:09 192.168.1.77 * *
"""

LOG = [
    "Nov  5 21:14:05 dnsmasq[1234]: query[A] redtube.com from 192.168.1.31",
    "Nov  5 21:14:05 dnsmasq[1234]: forwarded redtube.com to 1.1.1.1",
    "Nov  5 21:14:06 dnsmasq[1234]: query[AAAA] www.YouTube.com from 192.168.1.31",
    "Nov  5 21:14:07 dnsmasq[1234]: query[A] tiktok.com from 192.168.1.99",
]


def test_parse_leases():
    devs = parse_leases(LEASES, datetime(2026, 11, 5))
    assert [d.mac for d in devs] == ["a8:9c:ed:10:00:04", "da:4f:91:3e:7c:09"]
    assert devs[1].hostname == ""


def test_parse_query_log_maps_ip_to_mac_and_skips_noise():
    mac_by_ip = {d.ip: d.mac for d in parse_leases(LEASES, datetime(2026, 11, 5))}
    ev = list(parse_query_log(LOG, 2026, mac_by_ip))
    assert [(e.domain, e.mac) for e in ev] == [
        ("redtube.com", "a8:9c:ed:10:00:04"), ("www.youtube.com", "a8:9c:ed:10:00:04")]
    assert ev[0].ts == datetime(2026, 11, 5, 21, 14, 5)
