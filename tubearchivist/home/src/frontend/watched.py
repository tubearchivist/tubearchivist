"""
functionality:
- handle watched state for videos, channels and playlists
"""

import json
from datetime import datetime

import requests
from home.src.ta.config import AppConfig
from home.src.ta.helper import UrlListParser


class WatchState:
    """handle watched checkbox for videos and channels"""

    CONFIG = AppConfig().config
    ES_URL = CONFIG["application"]["es_url"]
    ES_AUTH = CONFIG["application"]["es_auth"]
    HEADERS = {"Content-type": "application/json"}

    def __init__(self, youtube_id):
        self.youtube_id = youtube_id
        self.stamp = int(datetime.now().strftime("%s"))

    def mark_as_watched(self):
        """update es with new watched value"""
        url_type = self.dedect_type()
        if url_type == "video":
            self.mark_vid_watched()
        elif url_type == "channel":
            self.mark_channel_watched()
        elif url_type == "playlist":
            self.mark_playlist_watched()

        print(f"marked {self.youtube_id} as watched")

    def mark_as_unwatched(self):
        """revert watched state to false"""
        url_type = self.dedect_type()
        if url_type == "video":
            self.mark_vid_watched(revert=True)

        print(f"revert {self.youtube_id} as unwatched")

    def dedect_type(self):
        """find youtube id type"""
        print(self.youtube_id)
        url_process = UrlListParser(self.youtube_id).process_list()
        url_type = url_process[0]["type"]
        return url_type

    def mark_vid_watched(self, revert=False):
        """change watched status of single video"""
        url = self.ES_URL + "/ta_video/_update/" + self.youtube_id
        data = {
            "doc": {"player": {"watched": True, "watched_date": self.stamp}}
        }
        if revert:
            data["doc"]["player"]["watched"] = False

        payload = json.dumps(data)
        request = requests.post(
            url, data=payload, headers=self.HEADERS, auth=self.ES_AUTH
        )
        if not request.ok:
            print(request.text)
            raise ValueError("failed to mark video as watched")

    def mark_channel_watched(self):
        """change watched status of every video in channel"""
        data = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "term": {
                                "channel.channel_id": {
                                    "value": self.youtube_id
                                }
                            }
                        },
                        {"term": {"player.watched": {"value": False}}},
                    ]
                }
            },
            "script": {
                "source": "ctx._source.player['watched'] = true",
                "lang": "painless",
            },
        }
        payload = json.dumps(data)
        url = f"{self.ES_URL}/ta_video/_update_by_query"
        request = requests.post(
            url, data=payload, headers=self.HEADERS, auth=self.ES_AUTH
        )
        if not request.ok:
            print(request.text)
            raise ValueError("failed mark channel as watched")

    def mark_playlist_watched(self):
        """change watched state of all videos in playlist"""
        data = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "term": {
                                "playlist.keyword": {"value": self.youtube_id}
                            }
                        },
                        {"term": {"player.watched": {"value": False}}},
                    ]
                }
            },
            "script": {
                "source": "ctx._source.player['watched'] = true",
                "lang": "painless",
            },
        }
        payload = json.dumps(data)
        url = f"{self.ES_URL}/ta_video/_update_by_query"
        request = requests.post(
            url, data=payload, headers=self.HEADERS, auth=self.ES_AUTH
        )
        if not request.ok:
            print(request.text)
            raise ValueError("failed mark playlist as watched")
