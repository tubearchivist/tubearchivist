"""build queries for video extraction from channel subscriptions"""

from download.src.yt_dlp_base import YtWrap
from video.src.constants import VideoTypeEnum


class VideoQueryBuilder:
    """Build queries for yt-dlp."""

    def __init__(self, config: dict, channel_overwrites: dict | None = None):
        self.config = config
        self.channel_overwrites = channel_overwrites or {}

    def build_queries(
        self, video_type: VideoTypeEnum | None, limit: bool = True
    ) -> list[tuple[VideoTypeEnum, int | None]]:
        """Build queries for all or specific video type."""
        query_methods = {
            VideoTypeEnum.VIDEOS: self.videos_query,
            VideoTypeEnum.STREAMS: self.streams_query,
            VideoTypeEnum.SHORTS: self.shorts_query,
        }

        if video_type:
            # build query for specific type
            query_method = query_methods.get(video_type)
            if query_method:
                query = query_method(limit)
                if query[1] != 0:
                    return [query]
                return []

        # Build and return queries for all video types
        queries = []
        for build_query in query_methods.values():
            query = build_query(limit)
            if query[1] != 0:
                queries.append(query)

        return queries

    def videos_query(self, limit: bool) -> tuple[VideoTypeEnum, int | None]:
        """Build query for videos."""
        return self._build_generic_query(
            video_type=VideoTypeEnum.VIDEOS,
            overwrite_key="subscriptions_channel_size",
            config_key="channel_size",
            limit=limit,
        )

    def streams_query(self, limit: bool) -> tuple[VideoTypeEnum, int | None]:
        """Build query for streams."""
        return self._build_generic_query(
            video_type=VideoTypeEnum.STREAMS,
            overwrite_key="subscriptions_live_channel_size",
            config_key="live_channel_size",
            limit=limit,
        )

    def shorts_query(self, limit: bool) -> tuple[VideoTypeEnum, int | None]:
        """Build query for shorts."""
        return self._build_generic_query(
            video_type=VideoTypeEnum.SHORTS,
            overwrite_key="subscriptions_shorts_channel_size",
            config_key="shorts_channel_size",
            limit=limit,
        )

    def _build_generic_query(
        self,
        video_type: VideoTypeEnum,
        overwrite_key: str,
        config_key: str,
        limit: bool,
    ) -> tuple[VideoTypeEnum, int | None]:
        """Generic query for video page scraping."""
        if not limit:
            return (video_type, None)

        if (
            overwrite_key in self.channel_overwrites
            and self.channel_overwrites[overwrite_key] is not None
        ):
            overwrite = self.channel_overwrites[overwrite_key]
            return (video_type, overwrite)

        if overwrite := self.config["subscriptions"].get(config_key):
            return (video_type, overwrite)

        return (video_type, 0)


def get_last_channel_videos(
    channel_id,
    config,
    limit=None,
    query_filter=None,
    channel_overwrites=None,
):
    """get a list of last videos from channel"""
    query_handler = VideoQueryBuilder(config, channel_overwrites)
    queries = query_handler.build_queries(query_filter)
    last_videos = []

    for vid_type_enum, limit_amount in queries:
        obs = {
            "skip_download": True,
            "extract_flat": True,
        }
        vid_type = vid_type_enum.value

        if limit is not None:
            obs.update({"playlist_items": f":{limit_amount}:1"})

        url = f"https://www.youtube.com/channel/{channel_id}/{vid_type}"
        channel_query, _ = YtWrap(obs, config).extract(url)
        if not channel_query:
            continue

        for entry in channel_query["entries"]:
            entry["vid_type"] = vid_type
            last_videos.append(entry)

    return last_videos
