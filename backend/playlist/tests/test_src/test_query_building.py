"""test playlist query building"""

import pytest
from playlist.src.query_building import QueryBuilder


def test_build_data():
    """test for correct key building"""
    qb = QueryBuilder(
        channel=["test_channel"],
        subscribed=["true"],
        type=["regular"],
    )
    result = qb.build_data()
    must_list = result["query"]["bool"]["must"]
    assert "query" in result
    assert "sort" in result
    assert result["sort"] == [{"playlist_name.keyword": {"order": "asc"}}]
    assert {"match": {"playlist_channel_id": "test_channel"}} in must_list
    assert {"match": {"playlist_subscribed": True}} in must_list


def test_parse_type():
    """validate type"""
    qb = QueryBuilder(type=["regular"])
    with pytest.raises(ValueError):
        qb.parse_type("invalid")

    result = qb.parse_type("custom")
    assert result == {"match": {"playlist_type.keyword": "custom"}}
