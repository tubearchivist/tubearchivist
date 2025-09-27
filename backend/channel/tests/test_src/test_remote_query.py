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
    result = builder.build_queries()
    expected = [
        (VideoTypeEnum.VIDEOS, 5),
        (VideoTypeEnum.STREAMS, 3),
        (VideoTypeEnum.SHORTS, 2),
    ]
    assert result == expected


def test_build_all_queries_without_limit(default_config, empty_overwrites):
    """limit disabled"""
    builder = VideoQueryBuilder(default_config, empty_overwrites, limit=False)
    result = builder.build_queries()
    expected = [
        (VideoTypeEnum.VIDEOS, None),
        (VideoTypeEnum.STREAMS, None),
        (VideoTypeEnum.SHORTS, None),
    ]
    assert result == expected


def test_build_specific_query(default_config, empty_overwrites):
    """single vid_type"""
    builder = VideoQueryBuilder(default_config, empty_overwrites)
    result = builder.build_query_type(VideoTypeEnum.VIDEOS)
    assert result == (VideoTypeEnum.VIDEOS, 5)


def test_build_unknown_type(default_config, empty_overwrites):
    """unknown vid_type build list"""
    builder = VideoQueryBuilder(default_config, empty_overwrites, limit=None)
    result = builder.build_queries()
    assert result == [
        (VideoTypeEnum.VIDEOS, None),
        (VideoTypeEnum.STREAMS, None),
        (VideoTypeEnum.SHORTS, None),
    ]


def test_build_multiple_queries(default_config, empty_overwrites):
    """vid_type list"""
    builder = VideoQueryBuilder(default_config, empty_overwrites)
    result = builder.build_queries(
        [VideoTypeEnum.VIDEOS, VideoTypeEnum.SHORTS]
    )
    assert result == [(VideoTypeEnum.VIDEOS, 5), (VideoTypeEnum.SHORTS, 2)]


def test_overwrite_applied(default_config, overwrites):
    """with overwrite from channel config"""
    builder = VideoQueryBuilder(default_config, overwrites)
    result = builder.build_queries()
    expected = [
        (VideoTypeEnum.VIDEOS, 10),  # Overwritten
        # STREAMS is overwritten to 0, should be excluded
        (VideoTypeEnum.SHORTS, 2),  # None in overwrite, fallback to config
    ]
    assert result == expected


def test_no_limit_ignores_config_and_overwrites(default_config, overwrites):
    """no limit single vid_type"""
    builder = VideoQueryBuilder(default_config, overwrites, limit=False)
    result = builder.build_queries([VideoTypeEnum.STREAMS])
    assert result == [(VideoTypeEnum.STREAMS, None)]


def test_zero_query_not_included(default_config):
    """overwrite to zero to disable"""
    overwrites = {"subscriptions_live_channel_size": 0}
    builder = VideoQueryBuilder(default_config, overwrites, limit=True)
    result = builder.build_queries([VideoTypeEnum.STREAMS])
    assert not result  # Should be skipped due to 0


def test_zero_config_overwrite(default_config):
    """zero default config but with overwrite"""
    new_default = default_config.copy()
    new_default["subscriptions"]["shorts_channel_size"] = 0
    new_overwrites = {
        "subscriptions_channel_size": 20,
        "subscriptions_live_channel_size": 20,
        "subscriptions_shorts_channel_size": 8,
    }

    builder = VideoQueryBuilder(new_default, new_overwrites, limit=True)
    result = builder.build_queries()
    assert result == [
        (VideoTypeEnum.VIDEOS, 20),
        (VideoTypeEnum.STREAMS, 20),
        (VideoTypeEnum.SHORTS, 8),
    ]


def test_invalid_video_type_is_ignored(default_config):
    """invalid enum"""
    builder = VideoQueryBuilder(default_config)

    class FakeEnum(Enum):
        """invalid"""

        INVALID = "invalid"

    result = builder.build_queries([FakeEnum.INVALID])
    assert not result
