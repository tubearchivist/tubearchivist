"""video constants"""

import enum


class VideoTypeEnum(enum.Enum):
    """all vid_type fields"""

    VIDEO = "video"
    LIVE = "live"
    SHORT = "short"
    UNKNOWN = "unknown"
