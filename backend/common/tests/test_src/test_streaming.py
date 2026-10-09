"""test streaming implementation"""

import pytest
from common.src.streaming import RangeNotSatisfiable, parse_range


@pytest.mark.parametrize(
    "range_header,file_size,expected",
    [
        ("bytes=0-0", 1000, (0, 0)),
        ("bytes=0-499", 1000, (0, 499)),
        ("bytes=500-", 1000, (500, 999)),
        ("bytes=-500", 1000, (500, 999)),
        ("bytes=-2000", 1000, (0, 999)),
        ("bytes=900-1200", 1000, (900, 999)),
        ("Bytes=1-2", 1000, (1, 2)),
    ],
)
def test_parse_range(range_header, file_size, expected):
    """parse supported single byte ranges"""
    assert parse_range(range_header, file_size) == expected


@pytest.mark.parametrize(
    "range_header",
    [
        None,
        "",
        "items=0-1",
        "bytes=",
        "bytes=-",
        "bytes=invalid-1",
        "bytes=1-invalid",
        "bytes=1-2-3",
        "bytes=0-1,2-3",
    ],
)
def test_parse_range_unsupported_returns_none(range_header):
    """ignore malformed and unsupported range requests"""
    assert parse_range(range_header, 1000) is None


@pytest.mark.parametrize(
    "range_header,file_size",
    [
        ("bytes=1000-", 1000),
        ("bytes=500-499", 1000),
        ("bytes=-0", 1000),
        ("bytes=0-0", 0),
        ("bytes=-1", 0),
    ],
)
def test_parse_range_not_satisfiable(range_header, file_size):
    """reject valid byte ranges that cannot be satisfied"""
    with pytest.raises(RangeNotSatisfiable):
        parse_range(range_header, file_size)
