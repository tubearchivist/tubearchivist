"""
functionality:
- handle watched state for videos, channels and playlists
"""

from datetime import datetime

from home.src.es.connect import ElasticWrap
from home.src.ta.helper import UrlListParser


class WatchState:
    """handle watched checkbox for videos and channels"""

    def __init__(self, youtube_id):
        self.youtube_id = youtube_id
        self.stamp = int(datetime.now().timestamp())

    def mark_as_watched(self):
        """update es with new watched value"""
        url_type = self.dedect_type()
        if url_type == "video":
            self.mark_vid_watched()
        elif url_type == "channel":
            self.mark_channel_watched()
        elif url_type == "playlist":
            self.mark_playlist_watched()

        print(f"{self.youtube_id}: marked as watched")

    def mark_as_unwatched(self):
        """revert watched state to false"""
        url_type = self.dedect_type()
        if url_type == "video":
            self.mark_vid_watched(revert=True)

        print(f"{self.youtube_id}: revert as unwatched")

    def dedect_type(self):
        """find youtube id type"""
        print(self.youtube_id)
        url_process = UrlListParser(self.youtube_id).process_list()
        url_type = url_process[0]["type"]
        return url_type

    def mark_vid_watched(self, revert=False):
        """change watched status of single video"""
        path = f"ta_video/_update/{self.youtube_id}"
        data = {
            "doc": {"player": {"watched": True, "watched_date": self.stamp}}
        }
        if revert:
            data["doc"]["player"]["watched"] = False

        response, status_code = ElasticWrap(path).post(data=data)
        if status_code != 200:
            print(response)
            raise ValueError("failed to mark video as watched")

    def _get_source(self):
        """build source line for update_by_query script"""
        source = [
            "ctx._source.player['watched'] = true",
            f"ctx._source.player['watched_date'] = {self.stamp}",
        ]
        return "; ".join(source)

    def mark_channel_watched(self):
        """change watched status of every video in channel"""
        path = "ta_video/_update_by_query"
        must_list = [
            {"term": {"channel.channel_id": {"value": self.youtube_id}}},
            {"term": {"player.watched": {"value": False}}},
        ]
        data = {
            "query": {"bool": {"must": must_list}},
            "script": {
                "source": self._get_source(),
                "lang": "painless",
            },
        }

        response, status_code = ElasticWrap(path).post(data=data)
        if status_code != 200:
            print(response)
            raise ValueError("failed mark channel as watched")

    def mark_playlist_watched(self):
        """change watched state of all videos in playlist"""
        path = "ta_video/_update_by_query"
        must_list = [
            {"term": {"playlist.keyword": {"value": self.youtube_id}}},
            {"term": {"player.watched": {"value": False}}},
        ]
        data = {
            "query": {"bool": {"must": must_list}},
            "script": {
                "source": self._get_source(),
                "lang": "painless",
            },
        }

        response, status_code = ElasticWrap(path).post(data=data)
        if status_code != 200:
            print(response)
            raise ValueError("failed mark playlist as watched")
