"""
functionality:
- get metadata from youtube for a video
- index and update in es
"""

import os
from datetime import datetime

import requests
from home.src.index import channel as ta_channel
from home.src.index.generic import YouTubeItem
from home.src.ta.helper import DurationConverter, clean_string
from ryd_client import ryd_client


class YoutubeVideo(YouTubeItem):
    """represents a single youtube video"""

    es_path = False
    index_name = "ta_video"
    yt_base = "https://www.youtube.com/watch?v="

    def __init__(self, youtube_id):
        super().__init__(youtube_id)
        self.channel_id = False
        self.es_path = f"{self.index_name}/_doc/{youtube_id}"

    def build_json(self):
        """build json dict of video"""
        self.get_from_youtube()
        if not self.youtube_meta:
            return

        self._process_youtube_meta()
        self._add_channel()
        self._add_stats()
        self.add_file_path()
        self.add_player()
        if self.config["downloads"]["integrate_ryd"]:
            self._get_ryd_stats()

        return

    def _process_youtube_meta(self):
        """extract relevant fields from youtube"""
        # extract
        self.channel_id = self.youtube_meta["channel_id"]
        upload_date = self.youtube_meta["upload_date"]
        upload_date_time = datetime.strptime(upload_date, "%Y%m%d")
        published = upload_date_time.strftime("%Y-%m-%d")
        last_refresh = int(datetime.now().strftime("%s"))
        # build json_data basics
        self.json_data = {
            "title": self.youtube_meta["title"],
            "description": self.youtube_meta["description"],
            "category": self.youtube_meta["categories"],
            "vid_thumb_url": self.youtube_meta["thumbnail"],
            "tags": self.youtube_meta["tags"],
            "published": published,
            "vid_last_refresh": last_refresh,
            "date_downloaded": last_refresh,
            "youtube_id": self.youtube_id,
            "active": True,
        }

    def _add_channel(self):
        """add channel dict to video json_data"""
        channel = ta_channel.YoutubeChannel(self.channel_id)
        channel.build_json(upload=True)
        self.json_data.update({"channel": channel.json_data})

    def _add_stats(self):
        """add stats dicst to json_data"""
        # likes
        like_count = self.youtube_meta.get("like_count", 0)
        dislike_count = self.youtube_meta.get("dislike_count", 0)
        self.json_data.update(
            {
                "stats": {
                    "view_count": self.youtube_meta["view_count"],
                    "like_count": like_count,
                    "dislike_count": dislike_count,
                    "average_rating": self.youtube_meta["average_rating"],
                }
            }
        )

    def build_dl_cache_path(self):
        """find video path in dl cache"""
        cache_dir = self.app_conf["cache_dir"]
        cache_path = f"{cache_dir}/download/"
        all_cached = os.listdir(cache_path)
        for file_cached in all_cached:
            if self.youtube_id in file_cached:
                vid_path = os.path.join(cache_path, file_cached)
                return vid_path

        return False

    def add_player(self):
        """add player information for new videos"""
        try:
            # when indexing from download task
            vid_path = self.build_dl_cache_path()
        except FileNotFoundError:
            # when reindexing
            base = self.app_conf["videos"]
            vid_path = os.path.join(base, self.json_data["media_url"])

        duration_handler = DurationConverter()
        duration = duration_handler.get_sec(vid_path)
        duration_str = duration_handler.get_str(duration)
        self.json_data.update(
            {
                "player": {
                    "watched": False,
                    "duration": duration,
                    "duration_str": duration_str,
                }
            }
        )

    def add_file_path(self):
        """build media_url for where file will be located"""
        channel_name = self.json_data["channel"]["channel_name"]
        clean_channel_name = clean_string(channel_name)
        if len(clean_channel_name) <= 3:
            # fall back to channel id
            clean_channel_name = self.json_data["channel"]["channel_id"]

        timestamp = self.json_data["published"].replace("-", "")
        youtube_id = self.json_data["youtube_id"]
        title = self.json_data["title"]
        clean_title = clean_string(title)
        filename = f"{timestamp}_{youtube_id}_{clean_title}.mp4"
        media_url = os.path.join(clean_channel_name, filename)
        self.json_data["media_url"] = media_url

    def delete_media_file(self):
        """delete video file, meta data"""
        self.get_from_es()
        video_base = self.app_conf["videos"]
        media_url = self.json_data["media_url"]
        print(f"{self.youtube_id}: delete {media_url} from file system")
        to_delete = os.path.join(video_base, media_url)
        os.remove(to_delete)
        self.del_in_es()

    def _get_ryd_stats(self):
        """get optional stats from returnyoutubedislikeapi.com"""
        try:
            print(f"{self.youtube_id}: get ryd stats")
            result = ryd_client.get(self.youtube_id)
        except requests.exceptions.ConnectionError:
            print(f"{self.youtube_id}: failed to query ryd api, skipping")
            return False

        if result["status"] == 404:
            return False

        dislikes = {
            "dislike_count": result["dislikes"],
            "average_rating": result["rating"],
        }
        self.json_data["stats"].update(dislikes)

        return True


def index_new_video(youtube_id):
    """combined classes to create new video in index"""
    video = YoutubeVideo(youtube_id)
    video.build_json()
    if not video.json_data:
        raise ValueError("failed to get metadata for " + youtube_id)

    video.upload_to_es()
    return video.json_data
