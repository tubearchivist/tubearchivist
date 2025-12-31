"""tests for search DSL parsing/building"""

import pytest
from common.src.searching import SearchParser


def test_tag_implies_video_mode():
    """tag: without explicit mode switches to video mode"""
    path, query, query_type = SearchParser("tag:music").run()
    assert query_type == "video"
    assert path == "ta_video/_search"
    assert query["query"]["bool"]["filter"]


def test_video_tag_or_filter_query_shape():
    """repeated tag: values OR together under query.bool.filter"""
    _, query, query_type = SearchParser("video:lofi tag:music tag:dance").run()
    assert query_type == "video"

    bool_query = query["query"]["bool"]
    assert "filter" in bool_query

    tag_filter = bool_query["filter"][0]["bool"]
    assert tag_filter["minimum_should_match"] == 1

    should = tag_filter["should"]
    assert len(should) == 2

    values = {clause["term"]["tags.keyword"]["value"] for clause in should}
    assert values == {"music", "dance"}


def test_video_tags_only_search():
    """tags-only search should work without a text term"""
    _, query, query_type = SearchParser("video: tag:music tag:dance").run()
    assert query_type == "video"

    bool_query = query["query"]["bool"]
    assert bool_query["must"] == []
    assert bool_query["filter"]


def test_tag_prefix_wildcard_builds_prefix_query():
    """trailing * builds a prefix query"""
    _, query, query_type = SearchParser("tag:music-*").run()
    assert query_type == "video"

    should = query["query"]["bool"]["filter"][0]["bool"]["should"]
    assert should == [{"prefix": {"tags.keyword": {"value": "music-"}}}]


def test_tag_invalid_wildcard_rejected():
    """leading wildcard is not supported"""
    with pytest.raises(ValueError, match=r"only trailing \* is supported"):
        SearchParser("tag:*music").run()


def test_tag_in_non_video_mode_rejected():
    """tag: is a video-only concept"""
    with pytest.raises(ValueError, match=r"only supported in video mode"):
        SearchParser("channel:linux tag:music").run()
