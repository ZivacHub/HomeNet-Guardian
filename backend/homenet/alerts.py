"""Alerts for the parent (filled in by plan step 1.6).

Contract the engine relies on (keep these signatures):
  on_new_device(conn, device_id, ts)                      a device the home has not seen joined
  on_approval_request(conn, request_id, device_id, domain, ts)   a store/payment request is waiting
  on_query(conn, device_row, event, decision)             after every stored lookup
  check_bypass(conn, now)                                 periodic check for DNS bypass
"""
from __future__ import annotations


def on_new_device(conn, device_id, ts) -> None:
    pass


def on_approval_request(conn, request_id, device_id, domain, ts) -> None:
    pass


def on_query(conn, device, event, decision) -> None:
    pass


def check_bypass(conn, now) -> None:
    pass
