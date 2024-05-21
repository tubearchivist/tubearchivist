"""
Functionality:
- processing search results for frontend
- this is duplicated code from home.src.frontend.searching.SearchHandler
"""

import urllib.parse

from home.src.download.thumbnails import ThumbManager
from home.src.ta.helper import date_parser, get_duration_str
from home.src.ta.settings import EnvironmentSettings


class SearchProcess:
    """process search results"""

    CACHE_DIR = EnvironmentSettings.CACHE_DIR

    def __init__(self, response):
        self.response = response
        self.processed = False

    def process(self):
        """detect type and process"""
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
        """detect which type of data to process"""
        index = result["_index"]
        processed = False
        if index == "ta_video":
            processed = self._process_video(result["_source"])
        if index == "ta_channel":
            processed = self._process_channel(result["_source"])
        if index == "ta_playlist":
            processed = self._process_playlist(result["_source"])
        if index == "ta_download":
            processed = self._process_download(result["_source"])
        if index == "ta_comment":
            processed = self._process_comment(result["_source"])
        if index == "ta_subtitle":
            processed = self._process_subtitle(result)

        if isinstance(processed, dict):
            processed.update(
                {
                    "_index": index,
                    "_score": round(result.get("_score") or 0, 2),
                }
            )

        return processed

    @staticmethod
    def _process_channel(channel_dict):
        """run on single channel"""
        channel_id = channel_dict["channel_id"]
        art_base = f"/cache/channels/{channel_id}"
        date_str = date_parser(channel_dict["channel_last_refresh"])
        channel_dict.update(
            {
                "channel_last_refresh": date_str,
                "channel_banner_url": f"{art_base}_banner.jpg",
                "channel_thumb_url": f"{art_base}_thumb.jpg",
                "channel_tvart_url": f"{art_base}_tvart.jpg",
            }
        )

        return dict(sorted(channel_dict.items()))

    def _process_video(self, video_dict):
        """run on single video dict"""
        video_id = video_dict["youtube_id"]
        media_url = urllib.parse.quote(video_dict["media_url"])
        vid_last_refresh = date_parser(video_dict["vid_last_refresh"])
        published = date_parser(video_dict["published"])
        vid_thumb_url = ThumbManager(video_id).vid_thumb_path()
        channel = self._process_channel(video_dict["channel"])

        if "subtitles" in video_dict:
            for idx, _ in enumerate(video_dict["subtitles"]):
                url = video_dict["subtitles"][idx]["media_url"]
                video_dict["subtitles"][idx]["media_url"] = f"/media/{url}"

        video_dict.update(
            {
                "channel": channel,
                "media_url": f"/media/{media_url}",
                "vid_last_refresh": vid_last_refresh,
                "published": published,
                "vid_thumb_url": f"{self.CACHE_DIR}/{vid_thumb_url}",
            }
        )

        return dict(sorted(video_dict.items()))

    @staticmethod
    def _process_playlist(playlist_dict):
        """run on single playlist dict"""
        playlist_id = playlist_dict["playlist_id"]
        playlist_last_refresh = date_parser(
            playlist_dict["playlist_last_refresh"]
        )
        playlist_dict.update(
            {
                "playlist_thumbnail": f"/cache/playlists/{playlist_id}.jpg",
                "playlist_last_refresh": playlist_last_refresh,
            }
        )

        return dict(sorted(playlist_dict.items()))

    def _process_download(self, download_dict):
        """run on single download item"""
        video_id = download_dict["youtube_id"]
        vid_thumb_url = ThumbManager(video_id).vid_thumb_path()
        published = date_parser(download_dict["published"])

        download_dict.update(
            {
                "vid_thumb_url": f"{self.CACHE_DIR}/{vid_thumb_url}",
                "published": published,
            }
        )
        return dict(sorted(download_dict.items()))

    def _process_comment(self, comment_dict):
        """run on all comments, create reply thread"""
        all_comments = comment_dict["comment_comments"]
        processed_comments = []

        for comment in all_comments:
            if comment["comment_parent"] == "root":
                comment.update({"comment_replies": []})
                processed_comments.append(comment)
            else:
                processed_comments[-1]["comment_replies"].append(comment)

        return processed_comments

    def _process_subtitle(self, result):
        """take complete result dict to extract highlight"""
        subtitle_dict = result["_source"]
        highlight = result.get("highlight")
        if highlight:
            # replace lines with the highlighted markdown
            subtitle_line = highlight.get("subtitle_line")[0]
            subtitle_dict.update({"subtitle_line": subtitle_line})

        thumb_path = ThumbManager(subtitle_dict["youtube_id"]).vid_thumb_path()
        subtitle_dict.update({"vid_thumb_url": f"/cache/{thumb_path}"})

        return subtitle_dict


def process_aggs(response):
    """convert aggs duration to str"""

    if response.get("aggregations"):
        aggs = response["aggregations"]
        if "total_duration" in aggs:
            duration_sec = int(aggs["total_duration"]["value"])
            aggs["total_duration"].update(
                {"value_str": get_duration_str(duration_sec)}
            )
