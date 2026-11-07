import csv
import gzip

import pytest

from homenet import categories as c
from homenet.categories import CATEGORIES, categorize, explicit_count, is_explicit


@pytest.mark.parametrize("domain,expected", [
    ("m.youtube.com", "video"),
    ("i.ytimg.com", "video"),
    ("youtube.com", "video"),
    ("a.b.googlevideo.com", "video"),
    ("www.tiktok.com", "social"),
    ("cdninstagram.com", "social"),
    ("store.steampowered.com", "payments"),
    ("steampowered.com", "games"),
    ("cdn.steampowered.com", "games"),
    ("play.google.com", "payments"),
    ("classroom.google.com", "learning"),
    ("google.com", "search"),
    ("mail.google.com", "messaging"),
    ("connectivitycheck.gstatic.com", "system"),
    ("dns.google", "encrypted_dns"),
    ("cloudflare-dns.com", "encrypted_dns"),
    ("mozilla.cloudflare-dns.com", "encrypted_dns"),
    ("WWW.Wikipedia.ORG.", "learning"),
    ("web.whatsapp.com", "messaging"),
    ("e-dnevnik.skole.hr", "learning"),
    ("open.spotify.com", "music"),
    ("unknown-site-xyz.example", "other"),
    ("", "other"),
])
def test_categorize(domain, expected):
    assert categorize(domain) == expected


def _explicit_lines():
    with gzip.open(c.EXPLICIT_GZ, "rt", encoding="utf-8") as fh:
        return [ln.strip() for ln in fh if ln.strip()]


def test_explicit_count():
    assert explicit_count() > 70000


def test_explicit_domains_from_file():
    lines = _explicit_lines()
    csv_domains = set(c._load_categories())
    picks = [d for d in (lines[0], lines[-1], lines[len(lines) // 2]) if d not in csv_domains]
    assert picks
    for d in picks:
        assert is_explicit(d)
        assert categorize(d) == "explicit"
        assert categorize("sub." + d) == "explicit"
        assert categorize("WWW." + d.upper() + ".") == "explicit"


def test_csv_overrides_explicit(monkeypatch):
    d = _explicit_lines()[100]
    assert categorize(d) == "explicit"
    monkeypatch.setattr(c, "_load_categories", lambda: {d: "news"})
    assert categorize(d) == "news"
    assert categorize("x." + d) == "news"


def test_csv_categories_valid():
    with open(c.CATEGORIES_CSV, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) >= 200
    assert {r["category"] for r in rows} <= set(CATEGORIES)
    domains = [r["domain"] for r in rows]
    assert len(domains) == len(set(domains))


def test_categories_constant():
    assert "explicit" in CATEGORIES and "other" in CATEGORIES and "encrypted_dns" in CATEGORIES
    assert len(CATEGORIES) == len(set(CATEGORIES)) == 14
