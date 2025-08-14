"""build query for video fetching"""

from common.src.ta_redis import RedisArchivist
from playlist.src.index import YoutubePlaylist
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
            must_list.append({"match": {"channel.channel_id": channel}})

        playlist = self.request_params.get("playlist")
        if playlist:
            must_list.append({"match": {"playlist.keyword": playlist}})

        watch = self.request_params.get("watch")
        if watch is not None:
            watch_must_list = self.parse_watch(watch)
            must_list.append(watch_must_list)

        video_type = self.request_params.get("type")
        if video_type:
            type_list_list = self.parse_type(video_type)
            must_list.append(type_list_list)

        height = self.request_params.get("height")
        if height:
            height_must = self.parse_height(height)
            must_list.append(height_must)

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

    def parse_height(self, height: str):
        """parse height to int"""

        return {"term": {"streams.height": {"value": height}}}

    def parse_sort(self) -> dict | None:
        """build sort key"""
        playlist = self.request_params.get("playlist")
        if playlist:
            # overwrite sort based on idx in playlist
            return self._get_playlist_sort(playlist_id=playlist)

        sort = self.request_params.get("sort")
        if not sort:
            return None

        if not hasattr(SortEnum, sort.upper()):
            raise ValueError(f"'{sort}' not in SortEnum")

        sort_field = getattr(SortEnum, sort.upper()).value

        order = self.request_params.get("order", "desc")
        if not hasattr(OrderEnum, order.upper()):
            raise ValueError(f"'{order}' not in OrderEnum")

        order_by = getattr(OrderEnum, order.upper()).value

        return {"sort": [{sort_field: {"order": order_by}}]}

    def _get_playlist_sort(self, playlist_id: str):
        """get sort for playlist"""
        playlist = YoutubePlaylist(playlist_id)
        playlist.get_from_es()
        if not playlist.json_data:
            raise ValueError(f"playlist {playlist_id} not found")

        sort_score = {
            i["youtube_id"]: i["idx"]
            for i in playlist.json_data["playlist_entries"]
            if i["downloaded"]
        }
        script = (
            "if(params.scores.containsKey(doc['youtube_id'].value)) "
            + "{return params.scores[doc['youtube_id'].value];} "
            + "return 100000;"
        )

        sort = {
            "sort": [
                {
                    "_script": {
                        "type": "number",
                        "script": {
                            "lang": "painless",
                            "source": script,
                            "params": {"scores": sort_score},
                        },
                        "order": "asc",
                    }
                }
            ],
        }

        return sort
