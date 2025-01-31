"""build query for video fetching"""

from common.src.ta_redis import RedisArchivist
from video.src.constants import OrderEnum, SortEnum, VideoTypeEnum


class QueryBuilder:
    """contain functionality"""

    WATCH_OPTIONS = ["watched", "unwatched", "continue"]

    def __init__(self, user_id: int, **kwargs):
        self.user_id = user_id
        self.request_params = kwargs

    def build_data(self) -> dict:
        """build data dict"""
        data = {}
        data["query"] = self.build_query()
        if sort := self.parse_sort():
            data.update(sort)

        return data

    def build_query(self) -> dict:
        """build query key"""
        must_list = []
        channel = self.request_params.get("channel")
        if channel:
            must_list.append({"match": {"channel.channel_id": channel[0]}})

        playlist = self.request_params.get("playlist")
        if playlist:
            must_list.append({"match": {"playlist.keyword": playlist[0]}})

        watch = self.request_params.get("watch")
        if watch:
            watch_must_list = self.parse_watch(watch[0])
            must_list.append(watch_must_list)

        video_type = self.request_params.get("type")
        if video_type:
            type_list_list = self.parse_type(video_type[0])
            must_list.append(type_list_list)

        query = {"bool": {"must": must_list}}

        return query

    def parse_watch(self, watch: str) -> dict:
        """build query"""
        if watch not in self.WATCH_OPTIONS:
            raise ValueError(f"'{watch}' not in {self.WATCH_OPTIONS}")

        if watch == "continue":
            continue_must = self._build_continue_must()
            return continue_must

        return {"match": {"player.watched": watch == "watched"}}

    def _build_continue_must(self):
        results = RedisArchivist().list_items(f"{self.user_id}:progress:")
        if not results:
            return None

        ids = [
            {"match": {"youtube_id": i.get("youtube_id")}}
            for i in results
            if not i.get("watched")
        ]
        if not ids:
            return None

        return {"bool": {"should": ids}}

    def parse_type(self, video_type: str):
        """parse video type"""
        if not hasattr(VideoTypeEnum, video_type.upper()):
            raise ValueError(f"'{video_type}' not in VideoTypeEnum")

        vid_type = getattr(VideoTypeEnum, video_type.upper()).value

        return {"match": {"vid_type": vid_type}}

    def parse_sort(self) -> dict | None:
        """build sort key"""
        sort = self.request_params.get("sort")
        if not sort:
            return None

        sort = sort[0]
        if not hasattr(SortEnum, sort.upper()):
            raise ValueError(f"'{sort}' not in SortEnum")

        sort_field = getattr(SortEnum, sort.upper()).value

        order = self.request_params.get("order", ["desc"])
        order = order[0]
        if not hasattr(OrderEnum, order.upper()):
            raise ValueError(f"'{order}' not in OrderEnum")

        order_by = getattr(OrderEnum, order.upper()).value

        return {"sort": [{sort_field: {"order": order_by}}]}
