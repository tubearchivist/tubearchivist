"""
functionality:
- handle watched state for videos, channels and playlists
"""

from datetime import datetime

from home.src.es.connect import ElasticWrap
from home.src.ta.urlparser import Parser


class WatchState:
    """handle watched checkbox for videos and channels"""

    def __init__(self, youtube_id, is_watched):
        self.youtube_id = youtube_id
        self.is_watched = is_watched
        self.stamp = int(datetime.now().timestamp())
        self.pipeline = f"_ingest/pipeline/watch_{youtube_id}"

    def change(self):
        """change watched state of item(s)"""
        print(f"{self.youtube_id}: change watched state to {self.is_watched}")
        url_type = self._dedect_type()
        if url_type == "video":
            self.change_vid_state()
            return

        self._add_pipeline()
        path = f"ta_video/_update_by_query?pipeline=watch_{self.youtube_id}"
        data = self._build_update_data(url_type)
        _, _ = ElasticWrap(path).post(data)
        self._delete_pipeline()

    def _dedect_type(self):
        """find youtube id type"""
        url_process = Parser(self.youtube_id).parse()
        url_type = url_process[0]["type"]
        return url_type

    def change_vid_state(self):
        """change watched state of video"""
        path = f"ta_video/_update/{self.youtube_id}"
        data = {
            "doc": {
                "player": {
                    "watched": self.is_watched,
                    "watched_date": self.stamp,
                }
            }
        }
        response, status_code = ElasticWrap(path).post(data=data)
        if status_code != 200:
            print(response)
            raise ValueError("failed to mark video as watched")

    def _build_update_data(self, url_type):
        """build update by query data based on url_type"""
        term_key_map = {
            "channel": "channel.channel_id",
            "playlist": "playlist.keyword",
        }
        term_key = term_key_map.get(url_type)

        return {
            "query": {
                "bool": {
                    "must": [
                        {"term": {term_key: {"value": self.youtube_id}}},
                        {
                            "term": {
                                "player.watched": {
                                    "value": not self.is_watched
                                }
                            }
                        },
                    ],
                }
            }
        }

    def _add_pipeline(self):
        """add ingest pipeline"""
        data = {
            "description": f"{self.youtube_id}: watched {self.is_watched}",
            "processors": [
                {
                    "set": {
                        "field": "player.watched",
                        "value": self.is_watched,
                    }
                },
                {
                    "set": {
                        "field": "player.watched_date",
                        "value": self.stamp,
                    }
                },
            ],
        }
        _, _ = ElasticWrap(self.pipeline).put(data)

    def _delete_pipeline(self):
        """delete pipeline"""
        ElasticWrap(self.pipeline).delete()
