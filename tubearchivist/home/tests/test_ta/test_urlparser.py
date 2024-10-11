"""tests for url parser"""

import pytest
from home.src.ta.urlparser import Parser

# video id parsing
VIDEO_URL_IN = [
    "7DKv5H5Frt0",
    "https://www.youtube.com/watch?v=7DKv5H5Frt0",
    "https://www.youtube.com/watch?v=7DKv5H5Frt0&t=113&feature=shared",
    "https://www.youtube.com/watch?v=7DKv5H5Frt0&list=PL96C35uN7xGJu6skU4TBYrIWxggkZBrF5&index=1&pp=iAQB"  # noqa: E501
    "https://youtu.be/7DKv5H5Frt0",
]
VIDEO_OUT = [{"type": "video", "url": "7DKv5H5Frt0", "vid_type": "unknown"}]
VIDEO_TEST_CASES = [(i, VIDEO_OUT) for i in VIDEO_URL_IN]

# shorts id parsing
SHORTS_URL_IN = [
    "https://www.youtube.com/shorts/YG3-Pw3rixU",
    "https://youtube.com/shorts/YG3-Pw3rixU?feature=shared",
]
SHORTS_OUT = [{"type": "video", "url": "YG3-Pw3rixU", "vid_type": "shorts"}]
SHORTS_TEST_CASES = [(i, SHORTS_OUT) for i in SHORTS_URL_IN]

# channel id parsing
CHANNEL_URL_IN = [
    "UCBa659QWEk1AI4Tg--mrJ2A",
    "@TomScottGo",
    "https://www.youtube.com/channel/UCBa659QWEk1AI4Tg--mrJ2A",
    "https://www.youtube.com/@TomScottGo",
]
CHANNEL_OUT = [
    {
        "type": "channel",
        "url": "UCBa659QWEk1AI4Tg--mrJ2A",
        "vid_type": "unknown",
    }
]
CHANNEL_TEST_CASES = [(i, CHANNEL_OUT) for i in CHANNEL_URL_IN]

# channel vid type parsing
CHANNEL_VID_TYPES = [
    (
        "https://www.youtube.com/@IBRACORP/videos",
        [
            {
                "type": "channel",
                "url": "UC7aW7chIafJG6ECYAd3N5uQ",
                "vid_type": "videos",
            }
        ],
    ),
    (
        "https://www.youtube.com/@IBRACORP/shorts",
        [
            {
                "type": "channel",
                "url": "UC7aW7chIafJG6ECYAd3N5uQ",
                "vid_type": "shorts",
            }
        ],
    ),
    (
        "https://www.youtube.com/@IBRACORP/streams",
        [
            {
                "type": "channel",
                "url": "UC7aW7chIafJG6ECYAd3N5uQ",
                "vid_type": "streams",
            }
        ],
    ),
]

# playlist id parsing
PLAYLIST_URL_IN = [
    "PL96C35uN7xGJu6skU4TBYrIWxggkZBrF5",
    "https://www.youtube.com/playlist?list=PL96C35uN7xGJu6skU4TBYrIWxggkZBrF5",
]
PLAYLIST_OUT = [
    {
        "type": "playlist",
        "url": "PL96C35uN7xGJu6skU4TBYrIWxggkZBrF5",
        "vid_type": "unknown",
    }
]
PLAYLIST_TEST_CASES = [(i, PLAYLIST_OUT) for i in PLAYLIST_URL_IN]

# personal playlists
EXPECTED_WL = [{"type": "playlist", "url": "WL", "vid_type": "unknown"}]
EXPECTED_LL = [{"type": "playlist", "url": "LL", "vid_type": "unknown"}]
PERSONAL_PLAYLISTS_TEST_CASES = [
    ("WL", EXPECTED_WL),
    ("https://www.youtube.com/playlist?list=WL", EXPECTED_WL),
    ("LL", EXPECTED_LL),
    ("https://www.youtube.com/playlist?list=LL", EXPECTED_LL),
]

# collect tests expected to pass
PASSTING_TESTS = []
PASSTING_TESTS.extend(VIDEO_TEST_CASES)
PASSTING_TESTS.extend(SHORTS_TEST_CASES)
PASSTING_TESTS.extend(CHANNEL_TEST_CASES)
PASSTING_TESTS.extend(CHANNEL_VID_TYPES)
PASSTING_TESTS.extend(PLAYLIST_TEST_CASES)
PASSTING_TESTS.extend(PERSONAL_PLAYLISTS_TEST_CASES)


@pytest.mark.parametrize("url_str, expected_result", PASSTING_TESTS)
def test_passing_parse(url_str, expected_result):
    """test parser"""
    parser = Parser(url_str)
    parsed = parser.parse()
    assert parsed == expected_result


INVALID_IDS_ERRORS = [
    "aaaaa",
    "https://www.youtube.com/playlist?list=AAAA",
    "https://www.youtube.com/channel/UC9-y-6csu5WGm29I7Jiwpn",
    "https://www.youtube.com/watch?v=CK3_zarXkw",
]


@pytest.mark.parametrize("invalid_value", INVALID_IDS_ERRORS)
def test_invalid_ids(invalid_value):
    """test for invalid IDs"""
    with pytest.raises(ValueError, match="not a valid id_str"):
        parser = Parser(invalid_value)
        parser.parse()


INVALID_DOMAINS = [
    "https://vimeo.com/32001208",
    "https://peertube.tv/w/8RiJE2j2nw569FVgPNjDt7",
]


@pytest.mark.parametrize("invalid_value", INVALID_DOMAINS)
def test_invalid_domains(invalid_value):
    """raise error on none YT domains"""
    parser = Parser(invalid_value)
    with pytest.raises(ValueError, match="invalid domain"):
        parser.parse()
