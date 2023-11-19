"""aggregations"""

from home.src.es.connect import ElasticWrap
from home.src.ta.helper import get_duration_str
from home.src.ta.settings import EnvironmentSettings


class AggBase:
    """base class for aggregation calls"""

    path: str = ""
    data: dict = {}
    name: str = ""

    def get(self):
        """make get call"""
        response, _ = ElasticWrap(self.path).get(self.data)
        print(f"[agg][{self.name}] took {response.get('took')} ms to process")

        return response.get("aggregations")

    def process(self):
        """implement in subclassess"""
        raise NotImplementedError


class Primary(AggBase):
    """primary aggregation for total documents indexed"""

    name = "primary"
    path = "ta_video,ta_channel,ta_playlist,ta_subtitle,ta_download/_search"
    data = {
        "size": 0,
        "aggs": {
            "video_type": {
                "filter": {"exists": {"field": "active"}},
                "aggs": {"filtered": {"terms": {"field": "vid_type"}}},
            },
            "channel_total": {"value_count": {"field": "channel_active"}},
            "channel_sub": {"terms": {"field": "channel_subscribed"}},
            "playlist_total": {"value_count": {"field": "playlist_active"}},
            "playlist_sub": {"terms": {"field": "playlist_subscribed"}},
            "download": {"terms": {"field": "status"}},
        },
    }

    def process(self):
        """make the call"""
        aggregations = self.get()

        videos = {"total": aggregations["video_type"].get("doc_count")}
        videos.update(
            {
                i.get("key"): i.get("doc_count")
                for i in aggregations["video_type"]["filtered"]["buckets"]
            }
        )
        channels = {"total": aggregations["channel_total"].get("value")}
        channels.update(
            {
                "sub_" + i.get("key_as_string"): i.get("doc_count")
                for i in aggregations["channel_sub"]["buckets"]
            }
        )
        playlists = {"total": aggregations["playlist_total"].get("value")}
        playlists.update(
            {
                "sub_" + i.get("key_as_string"): i.get("doc_count")
                for i in aggregations["playlist_sub"]["buckets"]
            }
        )
        downloads = {
            i.get("key"): i.get("doc_count")
            for i in aggregations["download"]["buckets"]
        }

        response = {
            "videos": videos,
            "channels": channels,
            "playlists": playlists,
            "downloads": downloads,
        }

        return response


class Video(AggBase):
    """get video stats"""

    name = "video_stats"
    path = "ta_video/_search"
    data = {
        "size": 0,
        "aggs": {
            "video_type": {
                "terms": {"field": "vid_type"},
                "aggs": {"media_size": {"sum": {"field": "media_size"}}},
            },
            "video_active": {
                "terms": {"field": "active"},
                "aggs": {"media_size": {"sum": {"field": "media_size"}}},
            },
            "video_media_size": {"sum": {"field": "media_size"}},
            "video_count": {"value_count": {"field": "youtube_id"}},
        },
    }

    def process(self):
        """process aggregation"""
        aggregations = self.get()

        response = {
            "doc_count": aggregations["video_count"]["value"],
            "media_size": int(aggregations["video_media_size"]["value"]),
        }
        for bucket in aggregations["video_type"]["buckets"]:
            response.update(
                {
                    f"type_{bucket['key']}": {
                        "doc_count": bucket.get("doc_count"),
                        "media_size": int(bucket["media_size"].get("value")),
                    }
                }
            )

        for bucket in aggregations["video_active"]["buckets"]:
            response.update(
                {
                    f"active_{bucket['key_as_string']}": {
                        "doc_count": bucket.get("doc_count"),
                        "media_size": int(bucket["media_size"].get("value")),
                    }
                }
            )

        return response


class Channel(AggBase):
    """get channel stats"""

    name = "channel_stats"
    path = "ta_channel/_search"
    data = {
        "size": 0,
        "aggs": {
            "channel_count": {"value_count": {"field": "channel_id"}},
            "channel_active": {"terms": {"field": "channel_active"}},
            "channel_subscribed": {"terms": {"field": "channel_subscribed"}},
        },
    }

    def process(self):
        """process aggregation"""
        aggregations = self.get()

        response = {
            "doc_count": aggregations["channel_count"].get("value"),
        }
        for bucket in aggregations["channel_active"]["buckets"]:
            key = f"active_{bucket['key_as_string']}"
            response.update({key: bucket.get("doc_count")})
        for bucket in aggregations["channel_subscribed"]["buckets"]:
            key = f"subscribed_{bucket['key_as_string']}"
            response.update({key: bucket.get("doc_count")})

        return response


class Playlist(AggBase):
    """get playlist stats"""

    name = "playlist_stats"
    path = "ta_playlist/_search"
    data = {
        "size": 0,
        "aggs": {
            "playlist_count": {"value_count": {"field": "playlist_id"}},
            "playlist_active": {"terms": {"field": "playlist_active"}},
            "playlist_subscribed": {"terms": {"field": "playlist_subscribed"}},
        },
    }

    def process(self):
        """process aggregation"""
        aggregations = self.get()
        response = {"doc_count": aggregations["playlist_count"].get("value")}
        for bucket in aggregations["playlist_active"]["buckets"]:
            key = f"active_{bucket['key_as_string']}"
            response.update({key: bucket.get("doc_count")})
        for bucket in aggregations["playlist_subscribed"]["buckets"]:
            key = f"subscribed_{bucket['key_as_string']}"
            response.update({key: bucket.get("doc_count")})

        return response


class Download(AggBase):
    """get downloads queue stats"""

    name = "download_queue_stats"
    path = "ta_download/_search"
    data = {
        "size": 0,
        "aggs": {
            "status": {"terms": {"field": "status"}},
            "video_type": {
                "filter": {"term": {"status": "pending"}},
                "aggs": {"type_pending": {"terms": {"field": "vid_type"}}},
            },
        },
    }

    def process(self):
        """process aggregation"""
        aggregations = self.get()
        response = {}
        for bucket in aggregations["status"]["buckets"]:
            response.update({bucket["key"]: bucket.get("doc_count")})

        for bucket in aggregations["video_type"]["type_pending"]["buckets"]:
            key = f"pending_{bucket['key']}"
            response.update({key: bucket.get("doc_count")})

        return response


class WatchProgress(AggBase):
    """get watch progress"""

    name = "watch_progress"
    path = "ta_video/_search"
    data = {
        "size": 0,
        "aggs": {
            name: {
                "terms": {"field": "player.watched"},
                "aggs": {
                    "watch_docs": {
                        "filter": {"terms": {"player.watched": [True, False]}},
                        "aggs": {
                            "true_count": {"value_count": {"field": "_index"}},
                            "duration": {"sum": {"field": "player.duration"}},
                        },
                    },
                },
            },
            "total_duration": {"sum": {"field": "player.duration"}},
            "total_vids": {"value_count": {"field": "_index"}},
        },
    }

    def process(self):
        """make the call"""
        aggregations = self.get()
        buckets = aggregations[self.name]["buckets"]

        response = {}
        all_duration = int(aggregations["total_duration"].get("value"))
        response.update(
            {
                "total": {
                    "duration": all_duration,
                    "duration_str": get_duration_str(all_duration),
                    "items": aggregations["total_vids"].get("value"),
                }
            }
        )

        for bucket in buckets:
            response.update(self._build_bucket(bucket, all_duration))

        return response

    @staticmethod
    def _build_bucket(bucket, all_duration):
        """parse bucket"""

        duration = int(bucket["watch_docs"]["duration"]["value"])
        duration_str = get_duration_str(duration)
        items = bucket["watch_docs"]["true_count"]["value"]
        if bucket["key_as_string"] == "false":
            key = "unwatched"
        else:
            key = "watched"

        bucket_parsed = {
            key: {
                "duration": duration,
                "duration_str": duration_str,
                "progress": duration / all_duration if all_duration else 0,
                "items": items,
            }
        }

        return bucket_parsed


class DownloadHist(AggBase):
    """get downloads histogram last week"""

    name = "videos_last_week"
    path = "ta_video/_search"
    data = {
        "size": 0,
        "aggs": {
            name: {
                "date_histogram": {
                    "field": "date_downloaded",
                    "calendar_interval": "day",
                    "format": "yyyy-MM-dd",
                    "order": {"_key": "desc"},
                    "time_zone": EnvironmentSettings.TZ,
                },
                "aggs": {
                    "total_videos": {"value_count": {"field": "youtube_id"}},
                    "media_size": {"sum": {"field": "media_size"}},
                },
            }
        },
        "query": {
            "range": {
                "date_downloaded": {
                    "gte": "now-7d/d",
                    "time_zone": EnvironmentSettings.TZ,
                }
            }
        },
    }

    def process(self):
        """process query"""
        aggregations = self.get()
        buckets = aggregations[self.name]["buckets"]

        response = [
            {
                "date": i.get("key_as_string"),
                "count": i.get("doc_count"),
                "media_size": i["media_size"].get("value"),
            }
            for i in buckets
        ]

        return response


class BiggestChannel(AggBase):
    """get channel aggregations"""

    def __init__(self, order):
        self.data["aggs"][self.name]["multi_terms"]["order"] = {order: "desc"}

    name = "channel_stats"
    path = "ta_video/_search"
    data = {
        "size": 0,
        "aggs": {
            name: {
                "multi_terms": {
                    "terms": [
                        {"field": "channel.channel_name.keyword"},
                        {"field": "channel.channel_id"},
                    ],
                    "order": {"doc_count": "desc"},
                },
                "aggs": {
                    "doc_count": {"value_count": {"field": "_index"}},
                    "duration": {"sum": {"field": "player.duration"}},
                    "media_size": {"sum": {"field": "media_size"}},
                },
            },
        },
    }
    order_choices = ["doc_count", "duration", "media_size"]

    def process(self):
        """process aggregation, order_by validated in the view"""

        aggregations = self.get()
        buckets = aggregations[self.name]["buckets"]

        response = [
            {
                "id": i["key"][1],
                "name": i["key"][0].title(),
                "doc_count": i["doc_count"]["value"],
                "duration": i["duration"]["value"],
                "duration_str": get_duration_str(int(i["duration"]["value"])),
                "media_size": i["media_size"]["value"],
            }
            for i in buckets
        ]

        return response
