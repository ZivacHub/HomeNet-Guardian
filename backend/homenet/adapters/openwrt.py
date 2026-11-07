"""How HomeNet Guardian would read a real OpenWrt router (described, not connected).

Status: NOT connected to a router in this project. The two parsers below read the formats
OpenWrt documents and are tested on sample lines only.

What the router provides
------------------------
* Devices: ``/tmp/dhcp.leases``, written by dnsmasq. One lease per line:
  ``<expiry-epoch> <mac> <ip> <hostname> <client-id>``
* Site-name lookups: dnsmasq with query logging enabled
  (``uci set dhcp.@dnsmasq[0].logqueries='1'``; optionally ``logfacility='/tmp/dnsmasq.log'``).
  Lines look like ``Nov  7 21:14:05 dnsmasq[1234]: query[A] redtube.com from 192.168.1.31``.
  The log names the client by IP, so the lease file maps IP -> MAC.
* Names inside encrypted connections (SNI): not logged by default; would need a small packet
  reader on the router (for example tcpdump/tshark on br-lan port 443) — optional.

How blocking would be applied on the router
-------------------------------------------
* Blocked sites: dnsmasq answers them with nothing (``address=/redtube.com/``), or an nftables
  set filled by dnsmasq (``nftset=/tiktok.com/4#inet#fw4#hg_block``) with a firewall rule that
  drops traffic to that set per device MAC.
* Schedules and pause: firewall rules per MAC with time matches, or the engine toggling the rule.
* Stop DNS bypass: redirect every DNS request (port 53) to the router
  (``fw4`` redirect rule), and block known encrypted-DNS servers (DoH/DoT, port 853).
  Devices that still have traffic but stop sending lookups are flagged as "possible bypass".
"""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Iterator

from .base import DeviceSeen, NetEvent

_QUERY_RE = re.compile(
    r"^(?P<mon>\w{3})\s+(?P<day>\d{1,2})\s+(?P<time>\d{2}:\d{2}:\d{2})\s+dnsmasq\[\d+\]:\s+"
    r"query\[(?P<qtype>[A-Z0-9]+)\]\s+(?P<domain>\S+)\s+from\s+(?P<ip>\S+)$"
)


def parse_leases(text: str, seen_at: datetime) -> list[DeviceSeen]:
    """Parse /tmp/dhcp.leases content."""
    out = []
    for line in text.splitlines():
        parts = line.split()
        if len(parts) < 4:
            continue
        _expiry, mac, ip, hostname = parts[:4]
        out.append(DeviceSeen(mac.lower(), "" if hostname == "*" else hostname, ip, seen_at))
    return out


def parse_query_log(lines: list[str], year: int, mac_by_ip: dict[str, str]) -> Iterator[NetEvent]:
    """Parse dnsmasq 'query[...]' log lines. Other dnsmasq lines (forwarded, reply) are skipped."""
    for line in lines:
        m = _QUERY_RE.match(line.strip())
        if not m or m["qtype"] not in ("A", "AAAA", "HTTPS"):
            continue
        mac = mac_by_ip.get(m["ip"])
        if mac is None:
            continue
        ts = datetime.strptime(f"{year} {m['mon']} {m['day']} {m['time']}", "%Y %b %d %H:%M:%S")
        yield NetEvent(ts, mac, m["domain"].lower(), "dns", 0)


class OpenWrtAdapter:
    """Reads lease and query-log files copied from (or mounted from) an OpenWrt router."""

    name = "openwrt"

    def __init__(self, leases_path: str | Path, query_log_path: str | Path, year: int) -> None:
        self.leases_path = Path(leases_path)
        self.query_log_path = Path(query_log_path)
        self.year = year

    def devices(self) -> list[DeviceSeen]:
        return parse_leases(self.leases_path.read_text(), datetime.now())

    def queries(self, since: datetime | None = None,
                until: datetime | None = None) -> Iterator[NetEvent]:
        mac_by_ip = {d.ip: d.mac for d in self.devices()}
        lines = self.query_log_path.read_text().splitlines()
        for e in parse_query_log(lines, self.year, mac_by_ip):
            if since is not None and e.ts <= since:
                continue
            if until is not None and e.ts > until:
                continue
            yield e
