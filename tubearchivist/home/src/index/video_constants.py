"""video constants"""

import enum


class VideoTypeEnum(enum.Enum):
    """all vid_type fields"""

    VIDEOS = "videos"
    STREAMS = "streams"
    SHORTS = "shorts"
    UNKNOWN = "unknown"
