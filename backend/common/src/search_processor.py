"""
Functionality:
- processing search results for frontend
- this is duplicated code from home.src.frontend.searching.SearchHandler
"""

import urllib.parse
from pathlib import Path

from common.src.helper import date_parser, get_duration_str
from common.src.ta_redis import RedisArchivist
from download.src.thumbnails import ThumbManager


class SearchProcess:
    """process search results"""

    def __init__(self, response, match_video_user_progress: None | int = None):
        self.response = response
        self.processed = False
        self.position_index = self.get_user_progress(match_video_user_progress)

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

    def get_user_progress(self, match_video_user_progress) -> dict | None:
        """get user video watch progress"""
        if not match_video_user_progress:
            return None

        query = f"{match_video_user_progress}:progress:*"
        all_positions = RedisArchivist().list_items(query)
        if not all_positions:
            return None

        pos_index = {
            i["youtube_id"]: i["position"]
            for i in all_positions
            if not i.get("watched")
        }
        return pos_index

    def _process_result(self, result):
        """detect which type of data to process"""
        index = result["_index"]
        processed = False
        if index.startswith("ta_video"):
            processed = self._process_video(result["_source"])
        if index.startswith("ta_channel"):
            processed = self._process_channel(result["_source"])
        if index.startswith("ta_playlist"):
            processed = self._process_playlist(result["_source"])
        if index.startswith("ta_download"):
            processed = self._process_download(result["_source"])
        if index.startswith("ta_comment"):
            processed = self._process_comment(result["_source"])
        if index.startswith("ta_subtitle"):
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
        art_base = f"/media/thumb/channel/{channel_id}"
        date_str = date_parser(channel_dict["channel_last_refresh"])
        channel_dict.update(
            {
                "channel_last_refresh": date_str,
                "channel_description": channel_dict.get("channel_description"),
            }
        )

        if channel_dict.get("channel_banner_url"):
            channel_dict["channel_banner_url"] = f"{art_base}/banner.jpg"
        else:
            channel_dict["channel_banner_url"] = None

        if channel_dict.get("channel_thumb_url"):
            channel_dict["channel_thumb_url"] = f"{art_base}/thumb.jpg"
        else:
            channel_dict["channel_thumb_url"] = None

        if channel_dict.get("channel_tvart_url"):
            channel_dict["channel_tvart_url"] = f"{art_base}/tvart.jpg"
        else:
            channel_dict["channel_tvart_url"] = None

        return dict(sorted(channel_dict.items()))

    def _process_video(self, video_dict):
        """run on single video dict"""
        video_id = video_dict["youtube_id"]
        media_url = urllib.parse.quote(video_dict["media_url"])
        vid_last_refresh = date_parser(video_dict["vid_last_refresh"])
        published = date_parser(video_dict["published"])
        channel = self._process_channel(video_dict["channel"])

        if "subtitles" in video_dict:
            for idx, _ in enumerate(video_dict["subtitles"]):
                url = video_dict["subtitles"][idx]["media_url"]
                subtitle_url = f"/media/subtitle/{url}"
                video_dict["subtitles"][idx]["media_url"] = subtitle_url
        else:
            video_dict["subtitles"] = []

        video_dict.update(
            {
                "channel": channel,
                "media_url": f"/media/stream/{media_url}",
                "vid_last_refresh": vid_last_refresh,
                "published": published,
                "vid_thumb_url": f"/media/thumb/video/{video_id}.jpg",
                "description": video_dict.get("description"),
            }
        )

        if self.position_index:
            player_position = self.position_index.get(video_id)
            total = video_dict["player"].get("duration")
            if player_position and total:
                progress = 100 * (player_position / total)
                video_dict["player"].update(
                    {
                        "progress": progress,
                        "position": player_position,
                    }
                )

        if "playlist" not in video_dict:
            video_dict["playlist"] = []

        return dict(sorted(video_dict.items()))

    def _process_playlist(self, playlist_dict):
        """run on single playlist dict"""
        playlist_last_refresh = date_parser(
            playlist_dict["playlist_last_refresh"]
        )
        playlist_thumbnail = self._playlist_thumb_vid_check(playlist_dict)
        description = playlist_dict.get("playlist_description")
        playlist_dict.update(
            {
                "playlist_thumbnail": playlist_thumbnail,
                "playlist_last_refresh": playlist_last_refresh,
                "playlist_description": description,
            }
        )

        return dict(sorted(playlist_dict.items()))

    @staticmethod
    def _playlist_thumb_vid_check(playlist_dict: dict):
        """use first video in playlist if available
        this is usually higher resolution"""
        entries = playlist_dict.get("playlist_entries", [])
        if len(entries) > 0 and entries[0]["downloaded"]:
            first_vid_id = entries[0]["youtube_id"]
            vid_path = ThumbManager(first_vid_id).vid_thumb_path(absolute=True)
            if Path(vid_path).exists():
                return f"/media/thumb/video/{first_vid_id}.jpg"

        return f"/media/thumb/playlist/{playlist_dict['playlist_id']}.jpg"

    def _process_download(self, download_dict):
        """run on single download item"""
        vid_thumb_url = None
        if download_dict.get("vid_thumb_url"):
            video_id = download_dict["youtube_id"]
            vid_thumb_path = Path(
                ThumbManager(item_id=video_id).vid_thumb_path(absolute=True)
            )
            if vid_thumb_path.exists():
                vid_thumb_url = f"/media/thumb/video/{video_id}.jpg"

        download_dict.update(
            {
                "vid_thumb_url": vid_thumb_url,
                "published": date_parser(download_dict["published"]),
            }
        )
        return dict(sorted(download_dict.items()))

    def _process_comment(self, comment_dict):
        """run on all comments, create reply thread"""
        comment_tree = []
        lookup = {}
        for comment in comment_dict["comment_comments"]:
            comment = comment.copy()
            comment["comment_replies"] = []
            lookup[comment["comment_id"]] = comment

        for comment in lookup.values():
            parent = comment.get("comment_parent")
            if parent == "root":
                comment_tree.append(comment)
            else:
                parent_node = lookup.get(parent)
                if parent_node:
                    parent_node["comment_replies"].append(comment)

        return comment_tree

    def _process_subtitle(self, result):
        """take complete result dict to extract highlight"""
        subtitle_dict = result["_source"]
        highlight = result.get("highlight")
        if highlight:
            # replace lines with the highlighted markdown
            subtitle_line = highlight.get("subtitle_line")[0]
            subtitle_dict.update({"subtitle_line": subtitle_line})

        video_id = subtitle_dict["youtube_id"]
        subtitle_dict.update(
            {"vid_thumb_url": f"/media/thumb/video/{video_id}.jpg"}
        )

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
