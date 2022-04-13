"""
Functionality:
- processing search results for frontend
- this is duplicated code from home.src.frontend.searching.SearchHandler
"""

import urllib.parse

from home.src.download.thumbnails import ThumbManager
from home.src.ta.helper import date_praser


class SearchProcess:
    """process search results"""

    def __init__(self, response):
        self.response = response
        self.processed = False

    def process(self):
        """dedect type and process"""
        if "_source" in self.response.keys():
            # single
            self.processed = self._process_result(self.response)

        elif "hits" in self.response.keys():
            # multiple
            self.processed = []
            all_sources = self.response["hits"]["hits"]
            for result in all_sources:
                self.processed.append(self._process_result(result))

        return self.processed

    def _process_result(self, result):
        """dedect which type of data to process"""
        index = result["_index"]
        processed = False
        if index == "ta_video":
            processed = self._process_video(result["_source"])
        if index == "ta_channel":
            processed = self._process_channel(result["_source"])
        if index == "ta_playlist":
            processed = self._process_playlist(result["_source"])

        return processed

    @staticmethod
    def _process_channel(channel_dict):
        """run on single channel"""
        channel_id = channel_dict["channel_id"]
        art_base = f"/cache/channels/{channel_id}"
        date_str = date_praser(channel_dict["channel_last_refresh"])
        channel_dict.update(
            {
                "channel_last_refresh": date_str,
                "channel_banner_url": f"{art_base}_banner.jpg",
                "channel_thumb_url": f"{art_base}_thumb.jpg",
                "channel_tvart_url": False,
            }
        )

        return dict(sorted(channel_dict.items()))

    def _process_video(self, video_dict):
        """run on single video dict"""
        video_id = video_dict["youtube_id"]
        media_url = urllib.parse.quote(video_dict["media_url"])
        vid_last_refresh = date_praser(video_dict["vid_last_refresh"])
        published = date_praser(video_dict["published"])
        vid_thumb_url = ThumbManager().vid_thumb_path(video_id)
        channel = self._process_channel(video_dict["channel"])

        video_dict.update(
            {
                "channel": channel,
                "media_url": media_url,
                "vid_last_refresh": vid_last_refresh,
                "published": published,
                "vid_thumb_url": vid_thumb_url,
            }
        )

        return dict(sorted(video_dict.items()))

    @staticmethod
    def _process_playlist(playlist_dict):
        """run on single playlist dict"""
        playlist_id = playlist_dict["playlist_id"]
        playlist_last_refresh = date_praser(
            playlist_dict["playlist_last_refresh"]
        )
        playlist_dict.update(
            {
                "playlist_thumbnail": f"/cache/playlists/{playlist_id}.jpg",
                "playlist_last_refresh": playlist_last_refresh,
            }
        )

        return dict(sorted(playlist_dict.items()))
