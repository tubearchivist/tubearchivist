"""aggregations"""

from home.src.es.connect import ElasticWrap
from home.src.index.video_streams import DurationConverter


class AggBase:
    """base class for aggregation calls"""

    path: str = ""
    data: dict = {}
    name: str = ""

    def get(self):
        """make get call"""
        data_size = {"size": 0, "aggs": self.data}
        response, _ = ElasticWrap(self.path).get(data_size)
        print(f"[agg][{self.name}] took {response.get('took')} ms to process")

        return response.get("aggregations")

    def process(self):
        """implement in subclassess"""
        raise NotImplementedError


class Primary(AggBase):
    """primary aggregation for total documents indexed"""

    name = "primary"
    path = "ta_video,ta_channel,ta_playlist,ta_subtitle,ta_download/_search"
    data = {name: {"terms": {"field": "_index"}}}

    def process(self):
        """make the call"""
        aggregations = self.get()
        buck = aggregations[self.name]["buckets"]

        return {i.get("key").lstrip("_ta"): i.get("doc_count") for i in buck}


class WatchProgress(AggBase):
    """get watch progress"""

    name = "watch_progress"
    path = "ta_video/_search"
    data = {
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
        }
    }

    def process(self):
        """make the call"""
        aggregations = self.get()
        buckets = aggregations[self.name]["buckets"]

        response = {}
        for bucket in buckets:
            response.update(self._build_bucket(bucket))

        return response

    @staticmethod
    def _build_bucket(bucket):
        """parse bucket"""

        duration = int(bucket["watch_docs"]["duration"]["value"])
        duration_str = DurationConverter().get_str(duration)
        items = bucket["watch_docs"]["true_count"]["value"]
        if bucket["key_as_string"] == "false":
            key = "unwatched"
        else:
            key = "watched"

        bucket_parsed = {
            key: {
                "duration": duration,
                "duration_str": duration_str,
                "items": items,
            }
        }

        return bucket_parsed
