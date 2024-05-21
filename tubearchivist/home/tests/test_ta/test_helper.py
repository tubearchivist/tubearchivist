"""tests for helper functions"""

import pytest
from home.src.ta.helper import (
    date_parser,
    get_duration_str,
    get_mapping,
    is_shorts,
    randomizor,
    time_parser,
)


def test_randomizor_with_positive_length():
    """test randomizer"""
    length = 10
    result = randomizor(length)
    assert len(result) == length
    assert result.isalnum()


def test_date_parser_with_int():
    """unix timestamp"""
    timestamp = 1621539600
    expected_date = "2021-05-20"
    assert date_parser(timestamp) == expected_date


def test_date_parser_with_str():
    """iso timestamp"""
    date_str = "2021-05-21"
    expected_date = "2021-05-21"
    assert date_parser(date_str) == expected_date


def test_date_parser_with_invalid_input():
    """invalid type"""
    invalid_input = [1621539600]
    with pytest.raises(TypeError):
        date_parser(invalid_input)


def test_date_parser_with_invalid_string_format():
    """invalid date string"""
    invalid_date_str = "21/05/2021"
    with pytest.raises(ValueError):
        date_parser(invalid_date_str)


def test_time_parser_with_numeric_string():
    """as number"""
    timestamp = "100"
    expected_seconds = 100
    assert time_parser(timestamp) == expected_seconds


def test_time_parser_with_hh_mm_ss_format():
    """to seconds"""
    timestamp = "01:00:00"
    expected_seconds = 3600.0
    assert time_parser(timestamp) == expected_seconds


def test_time_parser_with_empty_string():
    """handle empty"""
    timestamp = ""
    assert time_parser(timestamp) is False


def test_time_parser_with_invalid_format():
    """not enough to unpack"""
    timestamp = "01:00"
    with pytest.raises(ValueError):
        time_parser(timestamp)


def test_time_parser_with_non_numeric_input():
    """non numeric"""
    timestamp = "1a:00:00"
    with pytest.raises(ValueError):
        time_parser(timestamp)


def test_get_mapping():
    """test mappint"""
    index_config = get_mapping()
    assert isinstance(index_config, list)
    assert all(isinstance(i, dict) for i in index_config)


def test_is_shorts():
    """is shorts id"""
    youtube_id = "YG3-Pw3rixU"
    assert is_shorts(youtube_id)


def test_is_not_shorts():
    """is not shorts id"""
    youtube_id = "Ogr9kbypSNg"
    assert is_shorts(youtube_id) is False


def test_get_duration_str():
    """only seconds"""
    assert get_duration_str(None) == "NA"
    assert get_duration_str(5) == "5s"
    assert get_duration_str(10) == "10s"
    assert get_duration_str(500) == "8m 20s"
    assert get_duration_str(1000) == "16m 40s"
    assert get_duration_str(5000) == "1h 23m 20s"
    assert get_duration_str(500000) == "5d 18h 53m 20s"
    assert get_duration_str(5000000) == "57d 20h 53m 20s"
    assert get_duration_str(50000000) == "1y 213d 16h 53m 20s"
