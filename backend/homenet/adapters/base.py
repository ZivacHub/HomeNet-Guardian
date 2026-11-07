"""The data-source contract ("adapter").

The rules engine never talks to a router or a simulator directly. It asks an adapter two
questions, the same two a home router can answer:

* ``devices()``   - who is on the network (the router's DHCP leases)
* ``queries(since)`` - which site names they asked for (the DNS query log), plus site names
  seen at the start of encrypted connections (TLS SNI) where the router can see them.

The simulator answers them with a made-up family day; an OpenWrt router would answer them
from its dnsmasq log and lease file (see ``openwrt.py``). Nothing here reads page content.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterator, Literal, Protocol, runtime_checkable

Source = Literal["dns", "sni"]


@dataclass(frozen=True)
class DeviceSeen:
    """A device the router handed an address to (one DHCP lease)."""
    mac: str
    hostname: str
    ip: str
    first_seen: datetime
    kind_hint: str = "unknown"   # phone, tablet, laptop, tv, console, unknown


@dataclass(frozen=True)
class NetEvent:
    """One site-name lookup (dns) or one encrypted-connection name (sni)."""
    ts: datetime
    mac: str
    domain: str
    source: Source = "dns"
    bytes: int = 0               # data volume of the connection, when the source knows it


@runtime_checkable
class DataSource(Protocol):
    name: str

    def devices(self) -> list[DeviceSeen]:
        ...

    def queries(self, since: datetime | None = None,
                until: datetime | None = None) -> Iterator[NetEvent]:
        """Events with since < ts <= until, oldest first."""
        ...
