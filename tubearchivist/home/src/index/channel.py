"""
functionality:
- get metadata from youtube for a channel
- index and update in es
"""

import json
import os
from datetime import datetime

from home.src.download.thumbnails import ThumbManager
from home.src.download.yt_dlp_base import YtWrap
from home.src.es.connect import ElasticWrap, IndexPaginate
from home.src.index.generic import YouTubeItem
from home.src.index.playlist import YoutubePlaylist
from home.src.ta.settings import EnvironmentSettings


class YoutubeChannel(YouTubeItem):
    """represents a single youtube channel"""

    es_path = False
    index_name = "ta_channel"
    yt_base = "https://www.youtube.com/channel/"
    yt_obs = {
        "playlist_items": "1,0",
        "skip_download": True,
    }

    def __init__(self, youtube_id, task=False):
        super().__init__(youtube_id)
        self.all_playlists = False
        self.task = task

    def build_json(self, upload=False, fallback=False):
        """get from es or from youtube"""
        self.get_from_es()
        if self.json_data:
            return

        self.get_from_youtube()
        if not self.youtube_meta and fallback:
            self._video_fallback(fallback)
        else:
            self.process_youtube_meta()
            self.get_channel_art()

        if upload:
            self.upload_to_es()

    def process_youtube_meta(self):
        """extract relevant fields"""
        self.youtube_meta["thumbnails"].reverse()
        self.json_data = {
            "channel_active": True,
            "channel_description": self.youtube_meta.get("description", False),
            "channel_id": self.youtube_id,
            "channel_last_refresh": int(datetime.now().timestamp()),
            "channel_name": self.youtube_meta["uploader"],
            "channel_subs": self.youtube_meta.get("channel_follower_count", 0),
            "channel_subscribed": False,
            "channel_tags": self._parse_tags(self.youtube_meta.get("tags")),
            "channel_banner_url": self._get_banner_art(),
            "channel_thumb_url": self._get_thumb_art(),
            "channel_tvart_url": self._get_tv_art(),
            "channel_views": self.youtube_meta.get("view_count") or 0,
        }

    def _parse_tags(self, tags):
        """parse channel tags"""
        if not tags:
            return False

        joined = " ".join(tags)
        return [i.strip() for i in joined.split('"') if i and not i == " "]

    def _get_thumb_art(self):
        """extract thumb art"""
        for i in self.youtube_meta["thumbnails"]:
            if not i.get("width"):
                continue
            if i.get("width") == i.get("height"):
                return i["url"]

        return False

    def _get_tv_art(self):
        """extract tv artwork"""
        for i in self.youtube_meta["thumbnails"]:
            if i.get("id") == "banner_uncropped":
                return i["url"]
        for i in self.youtube_meta["thumbnails"]:
            if not i.get("width"):
                continue
            if i["width"] // i["height"] < 2 and not i["width"] == i["height"]:
                return i["url"]

        return False

    def _get_banner_art(self):
        """extract banner artwork"""
        for i in self.youtube_meta["thumbnails"]:
            if not i.get("width"):
                continue
            if i["width"] // i["height"] > 5:
                return i["url"]

        return False

    def _video_fallback(self, fallback):
        """use video metadata as fallback"""
        print(f"{self.youtube_id}: fallback to video metadata")
        self.json_data = {
            "channel_active": False,
            "channel_last_refresh": int(datetime.now().timestamp()),
            "channel_subs": fallback.get("channel_follower_count", 0),
            "channel_name": fallback["uploader"],
            "channel_banner_url": False,
            "channel_tvart_url": False,
            "channel_id": self.youtube_id,
            "channel_subscribed": False,
            "channel_tags": False,
            "channel_description": False,
            "channel_thumb_url": False,
            "channel_views": 0,
        }
        self._info_json_fallback()

    def _info_json_fallback(self):
        """read channel info.json for additional metadata"""
        info_json = os.path.join(
            EnvironmentSettings.CACHE_DIR,
            "import",
            f"{self.youtube_id}.info.json",
        )
        if os.path.exists(info_json):
            print(f"{self.youtube_id}: read info.json file")
            with open(info_json, "r", encoding="utf-8") as f:
                content = json.loads(f.read())

            self.json_data.update(
                {
                    "channel_subs": content.get("channel_follower_count", 0),
                    "channel_description": content.get("description", False),
                }
            )
            os.remove(info_json)

    def get_channel_art(self):
        """download channel art for new channels"""
        urls = (
            self.json_data["channel_thumb_url"],
            self.json_data["channel_banner_url"],
            self.json_data["channel_tvart_url"],
        )
        ThumbManager(self.youtube_id, item_type="channel").download(urls)

    def sync_to_videos(self):
        """sync new channel_dict to all videos of channel"""
        # add ingest pipeline
        processors = []
        for field, value in self.json_data.items():
            line = {"set": {"field": "channel." + field, "value": value}}
            processors.append(line)
        data = {"description": self.youtube_id, "processors": processors}
        ingest_path = f"_ingest/pipeline/{self.youtube_id}"
        _, _ = ElasticWrap(ingest_path).put(data)
        # apply pipeline
        data = {"query": {"match": {"channel.channel_id": self.youtube_id}}}
        update_path = f"ta_video/_update_by_query?pipeline={self.youtube_id}"
        _, _ = ElasticWrap(update_path).post(data)

    def get_folder_path(self):
        """get folder where media files get stored"""
        folder_path = os.path.join(
            EnvironmentSettings.MEDIA_DIR,
            self.json_data["channel_id"],
        )
        return folder_path

    def delete_es_videos(self):
        """delete all channel documents from elasticsearch"""
        data = {
            "query": {
                "term": {"channel.channel_id": {"value": self.youtube_id}}
            }
        }
        _, _ = ElasticWrap("ta_video/_delete_by_query").post(data)

    def delete_es_comments(self):
        """delete all comments from this channel"""
        data = {
            "query": {
                "term": {"comment_channel_id": {"value": self.youtube_id}}
            }
        }
        _, _ = ElasticWrap("ta_comment/_delete_by_query").post(data)

    def delete_es_subtitles(self):
        """delete all subtitles from this channel"""
        data = {
            "query": {
                "term": {"subtitle_channel_id": {"value": self.youtube_id}}
            }
        }
        _, _ = ElasticWrap("ta_subtitle/_delete_by_query").post(data)

    def delete_playlists(self):
        """delete all indexed playlist from es"""
        all_playlists = self.get_indexed_playlists()
        for playlist in all_playlists:
            YoutubePlaylist(playlist["playlist_id"]).delete_metadata()

    def delete_channel(self):
        """delete channel and all videos"""
        print(f"{self.youtube_id}: delete channel")
        self.get_from_es()
        if not self.json_data:
            raise FileNotFoundError

        folder_path = self.get_folder_path()
        print(f"{self.youtube_id}: delete all media files")
        try:
            all_videos = os.listdir(folder_path)
            for video in all_videos:
                video_path = os.path.join(folder_path, video)
                os.remove(video_path)
            os.rmdir(folder_path)
        except FileNotFoundError:
            print(f"no videos found for {folder_path}")

        print(f"{self.youtube_id}: delete indexed playlists")
        self.delete_playlists()
        print(f"{self.youtube_id}: delete indexed videos")
        self.delete_es_videos()
        self.delete_es_comments()
        self.delete_es_subtitles()
        self.del_in_es()

    def index_channel_playlists(self):
        """add all playlists of channel to index"""
        print(f"{self.youtube_id}: index all playlists")
        self.get_from_es()
        channel_name = self.json_data["channel_name"]
        self.task.send_progress([f"{channel_name}: Looking for Playlists"])
        self.get_all_playlists()
        if not self.all_playlists:
            print(f"{self.youtube_id}: no playlists found.")
            return

        total = len(self.all_playlists)
        for idx, playlist in enumerate(self.all_playlists):
            if self.task:
                self._notify_single_playlist(idx, total)

            self._index_single_playlist(playlist)
            print("add playlist: " + playlist[1])

    def _notify_single_playlist(self, idx, total):
        """send notification"""
        channel_name = self.json_data["channel_name"]
        message = [
            f"{channel_name}: Scanning channel for playlists",
            f"Progress: {idx + 1}/{total}",
        ]
        self.task.send_progress(message, progress=(idx + 1) / total)

    @staticmethod
    def _index_single_playlist(playlist):
        """add single playlist if needed"""
        playlist = YoutubePlaylist(playlist[0])
        playlist.update_playlist(skip_on_empty=True)

    def get_channel_videos(self):
        """get all videos from channel"""
        data = {
            "query": {
                "term": {"channel.channel_id": {"value": self.youtube_id}}
            },
            "_source": ["youtube_id", "vid_type"],
        }
        all_videos = IndexPaginate("ta_video", data).get_results()
        return all_videos

    def get_all_playlists(self):
        """get all playlists owned by this channel"""
        url = (
            f"https://www.youtube.com/channel/{self.youtube_id}"
            + "/playlists?view=1&sort=dd&shelf_id=0"
        )
        obs = {"skip_download": True, "extract_flat": True}
        playlists = YtWrap(obs, self.config).extract(url)
        all_entries = [(i["id"], i["title"]) for i in playlists["entries"]]
        self.all_playlists = all_entries

    def get_indexed_playlists(self, active_only=False):
        """get all indexed playlists from channel"""
        must_list = [
            {"term": {"playlist_channel_id": {"value": self.youtube_id}}}
        ]
        if active_only:
            must_list.append({"term": {"playlist_active": {"value": True}}})

        data = {"query": {"bool": {"must": must_list}}}

        all_playlists = IndexPaginate("ta_playlist", data).get_results()
        return all_playlists

    def get_overwrites(self) -> dict:
        """get all per channel overwrites"""
        return self.json_data.get("channel_overwrites", {})

    def set_overwrites(self, overwrites):
        """set per channel overwrites"""
        valid_keys = [
            "download_format",
            "autodelete_days",
            "index_playlists",
            "integrate_sponsorblock",
            "subscriptions_channel_size",
            "subscriptions_live_channel_size",
            "subscriptions_shorts_channel_size",
        ]

        to_write = self.json_data.get("channel_overwrites", {})
        for key, value in overwrites.items():
            if key not in valid_keys:
                raise ValueError(f"invalid overwrite key: {key}")
            elif value == "disable":
                to_write[key] = False
                continue
            elif value == "0":
                if key in to_write:
                    del to_write[key]
                continue
            elif value == "1":
                to_write[key] = True
                continue
            elif isinstance(value, int) and int(value) < 0:
                if key in to_write:
                    del to_write[key]
                continue
            elif value is not None and value != "":
                to_write.update({key: value})

        self.json_data["channel_overwrites"] = to_write


def channel_overwrites(channel_id, overwrites):
    """collection to overwrite settings per channel"""
    channel = YoutubeChannel(channel_id)
    channel.build_json()
    channel.set_overwrites(overwrites)
    channel.upload_to_es()
    channel.sync_to_videos()
