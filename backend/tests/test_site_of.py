from homenet.categories import site_of


def test_youtube_mobile():
    assert site_of("m.youtube.com") == "youtube.com"


def test_ytimg_and_googlevideo():
    assert site_of("i.ytimg.com") == "ytimg.com"
    assert site_of("rr3---sn.googlevideo.com") == "googlevideo.com"


def test_different_category_keeps_longer_key():
    assert site_of("store.steampowered.com") == "store.steampowered.com"
    assert site_of("cdn.steampowered.com") == "steampowered.com"


def test_unknown_last_two_labels():
    assert site_of("a.b.example.org") == "example.org"
    assert site_of("www.example.org") == "example.org"


def test_second_level_country():
    assert site_of("news.bbc.co.uk") == "bbc.co.uk"
