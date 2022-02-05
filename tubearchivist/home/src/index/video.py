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


class YoutubeSubtitle:
    """handle video subtitle functionality"""

    def __init__(self, config, youtube_meta, media_url, youtube_id):
        self.config = config
        self.youtube_meta = youtube_meta
        self.media_url = media_url
        self.youtube_id = youtube_id
        self.languages = False

    def sub_conf_parse(self):
        """add additional conf values to self"""
        languages_raw = self.config["downloads"]["subtitle"]
        self.languages = [i.strip() for i in languages_raw.split(",")]

    def get_subtitles(self):
        """check what to do"""
        self.sub_conf_parse()
        if not self.languages:
            # no subtitles
            return False

        relevant_subtitles = self.get_user_subtitles()
        if relevant_subtitles:
            return relevant_subtitles

        if self.config["downloads"]["subtitle_source"] == "auto":
            relevant_auto = self.get_auto_caption()
            return relevant_auto

        return False

    def get_auto_caption(self):
        """get auto_caption subtitles"""
        print(f"{self.youtube_id}: get auto generated subtitles")
        all_subtitles = self.youtube_meta.get("automatic_captions")

        if not all_subtitles:
            return False

        relevant_subtitles = []

        for lang in self.languages:
            media_url = self.media_url.replace(".mp4", f"-{lang}.vtt")
            all_formats = all_subtitles.get(lang)
            subtitle = [i for i in all_formats if i["ext"] == "vtt"][0]
            subtitle.update(
                {"lang": lang, "source": "auto", "media_url": media_url}
            )
            relevant_subtitles.append(subtitle)
            break

        return relevant_subtitles

    def _normalize_lang(self):
        """normalize country specific language keys"""
        all_subtitles = self.youtube_meta.get("subtitles")
        if not all_subtitles:
            return False

        all_keys = list(all_subtitles.keys())
        for key in all_keys:
            lang = key.split("-")[0]
            old = all_subtitles.pop(key)
            if lang == "live_chat":
                continue
            all_subtitles[lang] = old

        return all_subtitles

    def get_user_subtitles(self):
        """get subtitles uploaded from channel owner"""
        print(f"{self.youtube_id}: get user uploaded subtitles")
        all_subtitles = self._normalize_lang()
        if not all_subtitles:
            return False

        relevant_subtitles = []

        for lang in self.languages:
            media_url = self.media_url.replace(".mp4", f"-{lang}.vtt")
            all_formats = all_subtitles.get(lang)
            subtitle = [i for i in all_formats if i["ext"] == "vtt"][0]
            subtitle.update(
                {"lang": lang, "source": "user", "media_url": media_url}
            )
            relevant_subtitles.append(subtitle)
            break

        return relevant_subtitles

    def download_subtitles(self, relevant_subtitles):
        """download subtitle files to archive"""
        for subtitle in relevant_subtitles:
            dest_path = os.path.join(
                self.config["application"]["videos"], subtitle["media_url"]
            )
            response = requests.get(subtitle["url"])
            if response.ok:
                # create folder here for first video of channel
                os.makedirs(os.path.split(dest_path)[0], exist_ok=True)
                with open(dest_path, "w", encoding="utf-8") as subfile:
                    subfile.write(response.text)
            else:
                print(f"{self.youtube_id}: failed to download subtitle")


class YoutubeVideo(YouTubeItem, YoutubeSubtitle):
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
        self._check_subtitles()
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

        raise FileNotFoundError

    def add_player(self):
        """add player information for new videos"""
        try:
            # when indexing from download task
            vid_path = self.build_dl_cache_path()
        except FileNotFoundError:
            # when reindexing needs to handle title rename
            channel = os.path.split(self.json_data["media_url"])[0]
            channel_dir = os.path.join(self.app_conf["videos"], channel)
            all_files = os.listdir(channel_dir)
            for file in all_files:
                if self.youtube_id in file:
                    vid_path = os.path.join(channel_dir, file)
                    break
            else:
                raise FileNotFoundError

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

    def _check_subtitles(self):
        """optionally add subtitles"""
        handler = YoutubeSubtitle(
            self.config,
            self.youtube_meta,
            media_url=self.json_data["media_url"],
            youtube_id=self.youtube_id,
        )
        subtitles = handler.get_subtitles()
        if subtitles:
            self.json_data["subtitles"] = subtitles
            handler.download_subtitles(relevant_subtitles=subtitles)


def index_new_video(youtube_id):
    """combined classes to create new video in index"""
    video = YoutubeVideo(youtube_id)
    video.build_json()
    if not video.json_data:
        raise ValueError("failed to get metadata for " + youtube_id)

    video.upload_to_es()
    return video.json_data