"""video constants"""

import enum


class VideoTypeEnum(enum.Enum):
    """all vid_type fields"""

    VIDEOS = "videos"
    STREAMS = "streams"
    SHORTS = "shorts"
    UNKNOWN = "unknown"

    @classmethod
    def values(cls) -> list[str]:
        """value list"""
        return [i.value for i in cls]

    @classmethod
    def values_known(cls) -> list[str]:
        """values known"""
        return [i.value for i in cls if i.value != "unknown"]


class SortEnum(enum.Enum):
    """all sort by options"""

    PUBLISHED = "published"
    DOWNLOADED = "date_downloaded"
    VIEWS = "stats.view_count"
    LIKES = "stats.like_count"
    DURATION = "player.duration"
    MEDIASIZE = "media_size"
    WIDTH = "streams.width"
    HEIGHT = "streams.height"

    @classmethod
    def values(cls) -> list[str]:
        """value list"""
        return [i.value for i in cls]

    @classmethod
    def names(cls) -> list[str]:
        """name list"""
        return [i.name.lower() for i in cls]


class OrderEnum(enum.Enum):
    """all order by options"""

    ASC = "asc"
    DESC = "desc"

    @classmethod
    def values(cls) -> list[str]:
        """value list"""
        return [i.value for i in cls]


class WatchedEnum(enum.Enum):
    """watched state enum"""

    WATCHED = "watched"
    UNWATCHED = "unwatched"
    CONTINUE = "continue"

    @classmethod
    def values(cls) -> list[str]:
        """value list"""
        return [i.value for i in cls]
