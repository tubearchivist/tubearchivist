"""build channel nav"""

from common.src.es_connect import ElasticWrap


class ChannelNav:
    """get all nav items"""

    def __init__(self, channel_id):
        self.channel_id = channel_id

    def get_nav(self):
        """build nav items"""
        nav = {
            "has_pending": self._get_has_pending(),
            "has_playlists": self._get_has_playlists(),
        }
        nav.update(self._get_vid_types())
        return nav

    def _get_vid_types(self):
        """get available vid_types in given channel"""
        data = {
            "size": 0,
            "query": {
                "term": {"channel.channel_id": {"value": self.channel_id}}
            },
            "aggs": {"unique_values": {"terms": {"field": "vid_type"}}},
        }
        response, _ = ElasticWrap("ta_video/_search").get(data)
        buckets = response["aggregations"]["unique_values"]["buckets"]

        type_nav = {
            "has_videos": False,
            "has_streams": False,
            "has_shorts": False,
        }
        for bucket in buckets:
            if bucket["key"] == "videos":
                type_nav["has_videos"] = True
            if bucket["key"] == "streams":
                type_nav["has_streams"] = True
            if bucket["key"] == "shorts":
                type_nav["has_shorts"] = True

        return type_nav

    def _get_has_pending(self):
        """check if has pending videos in download queue"""
        data = {
            "size": 1,
            "query": {
                "bool": {
                    "must": [
                        {"term": {"status": {"value": "pending"}}},
                        {"term": {"channel_id": {"value": self.channel_id}}},
                    ]
                }
            },
            "_source": False,
        }
        response, _ = ElasticWrap("ta_download/_search").get(data=data)

        return bool(response["hits"]["hits"])

    def _get_has_playlists(self):
        """check if channel has playlists"""
        path = "ta_playlist/_search"
        data = {
            "size": 1,
            "query": {
                "term": {"playlist_channel_id": {"value": self.channel_id}}
            },
            "_source": False,
        }
        response, _ = ElasticWrap(path).get(data=data)

        return bool(response["hits"]["hits"])
