"""Rebuild data/explicit_domains.txt.gz from MIT-licensed hosts files.

Run:  python -m homenet.update_lists
Standard library only. Only MIT-licensed sources are used (see data/NOTICE.md).
"""
from __future__ import annotations

import gzip
import re
import sys
import urllib.request
from datetime import date
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
OUT_FILE = DATA_DIR / "explicit_domains.txt.gz"

SOURCES = [
    "https://raw.githubusercontent.com/StevenBlack/hosts/master/extensions/porn/sinfonietta/hosts",
    "https://raw.githubusercontent.com/StevenBlack/hosts/master/extensions/porn/clefspeare13/hosts",
    "https://raw.githubusercontent.com/StevenBlack/hosts/master/extensions/porn/bigdargon/hosts",
]

_SKIP = {"0.0.0.0", "localhost", "localhost.localdomain", "local", "broadcasthost",
         "ip6-localhost", "ip6-loopback"}
_DOMAIN_RE = re.compile(r"^[a-z0-9]([a-z0-9._-]*[a-z0-9])?$")


def parse_hosts(text: str) -> set[str]:
    """Extract domains from lines that start with '0.0.0.0 '."""
    out: set[str] = set()
    for line in text.splitlines():
        if not line.startswith("0.0.0.0 "):
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        d = parts[1].strip().lower().rstrip(".")
        if d in _SKIP or "." not in d or not _DOMAIN_RE.match(d):
            continue
        out.add(d)
    return out


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "homenet-guardian-update"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode("utf-8", errors="replace")


def build(out_file: Path = OUT_FILE) -> int:
    domains: set[str] = set()
    for url in SOURCES:
        found = parse_hosts(fetch(url))
        print(f"{len(found):>7} domains from {url}")
        domains |= found
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(out_file, "wt", encoding="utf-8", newline="\n") as fh:
        for d in sorted(domains):
            fh.write(d + "\n")
    print(f"Wrote {len(domains)} domains to {out_file} on {date.today().isoformat()}")
    return len(domains)


def main() -> int:
    build()
    return 0


if __name__ == "__main__":
    sys.exit(main())
