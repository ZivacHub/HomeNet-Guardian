"""Site-category lookup: map a domain name to a coarse category."""
from __future__ import annotations

import csv
import gzip
from functools import lru_cache
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
CATEGORIES_CSV = DATA_DIR / "categories.csv"
EXPLICIT_GZ = DATA_DIR / "explicit_domains.txt.gz"

SOCIAL = "social"
VIDEO = "video"
GAMES = "games"
LEARNING = "learning"
MESSAGING = "messaging"
MUSIC = "music"
PAYMENTS = "payments"
SHOPPING = "shopping"
NEWS = "news"
SEARCH = "search"
SYSTEM = "system"
ENCRYPTED_DNS = "encrypted_dns"
EXPLICIT = "explicit"
OTHER = "other"

CATEGORIES = (SOCIAL, VIDEO, GAMES, LEARNING, MESSAGING, MUSIC, PAYMENTS, SHOPPING,
              NEWS, SEARCH, SYSTEM, ENCRYPTED_DNS, EXPLICIT, OTHER)


@lru_cache(maxsize=1)
def _load_categories() -> dict[str, str]:
    table: dict[str, str] = {}
    with open(CATEGORIES_CSV, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            table[row["domain"].strip().lower()] = row["category"].strip()
    return table


@lru_cache(maxsize=1)
def _load_explicit() -> frozenset[str]:
    with gzip.open(EXPLICIT_GZ, "rt", encoding="utf-8") as fh:
        return frozenset(line.strip() for line in fh if line.strip())


def _normalize(domain: str) -> str:
    d = (domain or "").strip().lower().rstrip(".")
    if d.startswith("www."):
        d = d[4:]
    return d


def _candidates(d: str):
    """Yield d, then each parent domain, longest first (never a bare TLD)."""
    while d:
        yield d
        _, _, d = d.partition(".")
        if "." not in d:
            return


def is_explicit(domain: str) -> bool:
    explicit = _load_explicit()
    return any(c in explicit for c in _candidates(_normalize(domain)))


def explicit_count() -> int:
    return len(_load_explicit())


def categorize(domain: str) -> str:
    d = _normalize(domain)
    if not d:
        return OTHER
    table = _load_categories()
    for cand in _candidates(d):
        cat = table.get(cand)
        if cat:
            return cat
    if is_explicit(d):
        return EXPLICIT
    return OTHER


_SECOND_LEVELS = frozenset({"co", "com", "org", "net", "gov", "ac", "edu"})


def site_of(domain: str) -> str:
    """The "site" a domain belongs to, for top-sites lists (m.youtube.com -> youtube.com)."""
    d = _normalize(domain)
    if not d:
        return ""
    table = _load_categories()
    matches = [c for c in _candidates(d) if c in table]
    if matches:
        cat = table[matches[0]]
        same = [c for c in matches if table[c] == cat]
        return min(same, key=len)
    labels = d.split(".")
    if len(labels) <= 2:
        return d
    if labels[-2] in _SECOND_LEVELS and len(labels[-1]) == 2:
        return ".".join(labels[-3:])
    return ".".join(labels[-2:])
