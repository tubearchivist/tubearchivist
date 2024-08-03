"""test video query building"""

import pytest
from video.src.query_building import QueryBuilder


def test_initialization():
    """init constructor"""
    qb = QueryBuilder(user_id=1)
    assert qb.user_id == 1
    assert not qb.request_params


def test_build_data():
    """test for correct key building"""
    qb = QueryBuilder(
        user_id=1,
        channel=["test_channel"],
        playlist=["test_playlist"],
        watch=["watched"],
        type=["videos"],
        sort=["published"],
        order=["desc"],
    )
    result = qb.build_data()
    assert "query" in result
    assert "sort" in result
    assert result["sort"] == [{"published": {"order": "desc"}}]


def test_parse_watch():
    """watched query building"""
    qb = QueryBuilder(user_id=1, watch=["watched"])
    result = qb.parse_watch("watched")
    assert result == {"match": {"player.watched": True}}

    result = qb.parse_watch("unwatched")
    assert result == {"match": {"player.watched": False}}

    with pytest.raises(ValueError):
        qb.parse_watch("invalid")


def test_parse_type():
    """test type is parsed"""
    qb = QueryBuilder(user_id=1, type=["videos"])
    with pytest.raises(ValueError):
        qb.parse_type("invalid")

    result = qb.parse_type("videos")
    assert result == {"match": {"vid_type": "videos"}}


def test_parse_sort():
    """test sort and order"""
    qb = QueryBuilder(user_id=1, sort=["views"], order=["desc"])
    result = qb.parse_sort()
    assert result == {"sort": [{"stats.view_count": {"order": "desc"}}]}

    with pytest.raises(ValueError):
        qb = QueryBuilder(user_id=1, sort=["invalid"])
        qb.parse_sort()

    with pytest.raises(ValueError):
        qb = QueryBuilder(
            user_id=1, sort=["stats.view_count"], order=["invalid"]
        )
        qb.parse_sort()
