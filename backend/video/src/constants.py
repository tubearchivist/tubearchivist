"""video constants"""

import enum


class VideoTypeEnum(enum.Enum):
    """all vid_type fields"""

    VIDEOS = "videos"
    STREAMS = "streams"
    SHORTS = "shorts"
    UNKNOWN = "unknown"


class SortEnum(enum.Enum):
    """all sort by options"""

    PUBLISHED = "published"
    DOWNLOADED = "date_downloaded"
    VIEWS = "stats.view_count"
    LIKES = "stats.like_count"
    DURATION = "player.duration"
    MEDIASIZE = "media_size"


class OrderEnum(enum.Enum):
    """all order by options"""

    ASC = "asc"
    DESC = "desc"
