"""build queries for video extraction from channel subscriptions"""

from appsettings.src.config import AppConfigType
from download.src.yt_dlp_base import YtWrap
from video.src.constants import VideoTypeEnum


class VideoQueryBuilder:
    """
    Build queries for yt-dlp.
    limit:
    - None: no limit
    - bool: limit lookup from overwrite or config if True
    - int: limit as int direct
    """

    MAPPING = {
        VideoTypeEnum.VIDEOS: {
            "config_key": "channel_size",
            "overwrite_key": "subscriptions_channel_size",
        },
        VideoTypeEnum.SHORTS: {
            "config_key": "shorts_channel_size",
            "overwrite_key": "subscriptions_shorts_channel_size",
        },
        VideoTypeEnum.STREAMS: {
            "config_key": "live_channel_size",
            "overwrite_key": "subscriptions_live_channel_size",
        },
    }

    def __init__(
        self,
        config: AppConfigType,
        channel_overwrites: dict | None = None,
        limit: None | bool | int = True,
    ):
        self.config = config
        self.channel_overwrites = channel_overwrites or {}
        self.limit = limit

    def build_queries(
        self,
        vid_types: list[VideoTypeEnum] = VideoTypeEnum.known(),
    ) -> list[tuple[VideoTypeEnum, int | None]]:
        """build queries"""
        queries: list[tuple[VideoTypeEnum, int | None]] = []
        for vid_type in vid_types:
            if vid_type not in self.MAPPING:
                continue

            query = self.build_query_type(vid_type)
            if query:
                queries.append(query)

        return queries

    def build_query_type(
        self,
        vid_type: VideoTypeEnum,
    ) -> tuple[VideoTypeEnum, int | None] | None:
        """build query for vid_type"""
        if self.limit is None:
            return (vid_type, None)

        if isinstance(self.limit, bool):
            if self.limit is False:
                return (vid_type, None)

            overwrite_key = self.MAPPING[vid_type]["overwrite_key"]
            overwrite = self.channel_overwrites.get(overwrite_key)
            if overwrite == 0:
                return None

            if overwrite:
                return (vid_type, overwrite)

            config_key = self.MAPPING[vid_type]["config_key"]
            app_config = self.config["subscriptions"].get(config_key)
            if app_config == 0:
                return None

            if app_config:
                return (vid_type, app_config)  # type: ignore

            return (vid_type, None)

        if isinstance(self.limit, int):
            return (vid_type, self.limit)

        return (vid_type, None)


def get_last_channel_videos(
    channel_id: str,
    config: AppConfigType,
    limit: None | bool | int = None,
    query_filter: VideoTypeEnum | list[VideoTypeEnum] | None = None,
) -> list[dict]:
    """get a list of last videos from channel"""

    builder = VideoQueryBuilder(config, limit=limit)

    queries = []
    if query_filter is None or query_filter == VideoTypeEnum.UNKNOWN:
        queries = builder.build_queries()
    elif isinstance(query_filter, list):
        queries = builder.build_queries(vid_types=query_filter)
    else:
        query = builder.build_query_type(vid_type=query_filter)
        if query:
            queries.append(query)

    last_videos: list[dict] = []

    if not queries:
        return last_videos

    for vid_type_enum, limit_amount in queries:
        obs: dict[str, bool | str] = {
            "skip_download": True,
            "extract_flat": True,
        }
        vid_type = vid_type_enum.value

        if limit is not None:
            obs["playlist_items"] = f":{limit_amount}:1"

        url = f"https://www.youtube.com/channel/{channel_id}/{vid_type}"
        channel_query, _ = YtWrap(obs, config).extract(url)
        if not channel_query:
            continue

        for entry in channel_query["entries"]:
            entry["vid_type"] = vid_type
            last_videos.append(entry)

    return last_videos
