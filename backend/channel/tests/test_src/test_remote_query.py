"""test video query building"""

# pylint: disable=redefined-outer-name

from enum import Enum

import pytest
from channel.src.remote_query import VideoQueryBuilder
from video.src.constants import VideoTypeEnum


@pytest.fixture
def default_config():
    """from appsettings"""
    return {
        "subscriptions": {
            "channel_size": 5,
            "live_channel_size": 3,
            "shorts_channel_size": 2,
        }
    }


@pytest.fixture
def empty_overwrites():
    """from channel overwrites"""
    return {}


@pytest.fixture
def overwrites():
    """from channel overwrites"""
    return {
        "subscriptions_channel_size": 10,
        "subscriptions_live_channel_size": 0,
        "subscriptions_shorts_channel_size": None,
    }


def test_build_all_queries_with_limit(default_config, empty_overwrites):
    """default, empty overwrite"""
    builder = VideoQueryBuilder(default_config, empty_overwrites)
    result = builder.build_queries(None, limit=True)
    expected = [
        (VideoTypeEnum.VIDEOS, 5),
        (VideoTypeEnum.STREAMS, 3),
        (VideoTypeEnum.SHORTS, 2),
    ]
    assert result == expected


def test_build_all_queries_without_limit(default_config, empty_overwrites):
    """limit disabled"""
    builder = VideoQueryBuilder(default_config, empty_overwrites)
    result = builder.build_queries(None, limit=False)
    expected = [
        (VideoTypeEnum.VIDEOS, None),
        (VideoTypeEnum.STREAMS, None),
        (VideoTypeEnum.SHORTS, None),
    ]
    assert result == expected


def test_build_specific_query(default_config, empty_overwrites):
    """single vid_type"""
    builder = VideoQueryBuilder(default_config, empty_overwrites)
    result = builder.build_queries(VideoTypeEnum.VIDEOS)
    assert result == [(VideoTypeEnum.VIDEOS, 5)]


def test_build_multiple_queries(default_config, empty_overwrites):
    """vid_type list"""
    builder = VideoQueryBuilder(default_config, empty_overwrites)
    result = builder.build_queries(
        [VideoTypeEnum.VIDEOS, VideoTypeEnum.SHORTS]
    )
    assert result == [(VideoTypeEnum.VIDEOS, 5), (VideoTypeEnum.SHORTS, 2)]


def test_build_unknown_queries(default_config, empty_overwrites):
    """vid_type unknown"""
    builder = VideoQueryBuilder(default_config, empty_overwrites)
    result = builder.build_queries(VideoTypeEnum.UNKNOWN)
    assert result == [
        (VideoTypeEnum.VIDEOS, 5),
        (VideoTypeEnum.STREAMS, 3),
        (VideoTypeEnum.SHORTS, 2),
    ]


def test_overwrite_applied(default_config, overwrites):
    """with overwrite from channel config"""
    builder = VideoQueryBuilder(default_config, overwrites)
    result = builder.build_queries(None, limit=True)
    expected = [
        (VideoTypeEnum.VIDEOS, 10),  # Overwritten
        # STREAMS is overwritten to 0, should be excluded
        (VideoTypeEnum.SHORTS, 2),  # None in overwrite, fallback to config
    ]
    assert result == expected


def test_no_limit_ignores_config_and_overwrites(default_config, overwrites):
    """no limit single vid_type"""
    builder = VideoQueryBuilder(default_config, overwrites)
    result = builder.build_queries([VideoTypeEnum.STREAMS], limit=False)
    assert result == [(VideoTypeEnum.STREAMS, None)]


def test_zero_query_not_included(default_config):
    """overwrite to zero to disable"""
    overwrites = {"subscriptions_live_channel_size": 0}
    builder = VideoQueryBuilder(default_config, overwrites)
    result = builder.build_queries([VideoTypeEnum.STREAMS], limit=True)
    assert not result  # Should be skipped due to 0


def test_invalid_video_type_is_ignored(default_config):
    """invalid enum"""
    builder = VideoQueryBuilder(default_config)

    class FakeEnum(Enum):
        """invalid"""

        INVALID = "invalid"

    result = builder.build_queries([FakeEnum.INVALID], limit=True)
    assert not result
