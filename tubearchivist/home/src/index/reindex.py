"""
functionality:
- periodically refresh documents
- index and update in es
"""

import os
import shutil
from datetime import datetime
from math import ceil
from time import sleep

from home.src.download.queue import PendingList
from home.src.download.thumbnails import ThumbManager
from home.src.download.yt_dlp_base import CookieHandler
from home.src.download.yt_dlp_handler import VideoDownloader
from home.src.es.connect import ElasticWrap
from home.src.index.channel import YoutubeChannel
from home.src.index.playlist import YoutubePlaylist
from home.src.index.video import YoutubeVideo
from home.src.ta.config import AppConfig


class Reindex:
    """check for outdated documents and refresh data from youtube"""

    MATCH_FIELD = {
        "ta_video": "active",
        "ta_channel": "channel_active",
        "ta_playlist": "playlist_active",
    }
    MULTIPLY = 1.2

    def __init__(self):
        # config
        self.now = int(datetime.now().strftime("%s"))
        self.config = AppConfig().config
        self.interval = self.config["scheduler"]["check_reindex_days"]
        # scan
        self.all_youtube_ids = False
        self.all_channel_ids = False
        self.all_playlist_ids = False

    def check_cookie(self):
        """validate cookie if enabled"""
        if self.config["downloads"]["cookie_import"]:
            valid = CookieHandler(self.config).validate()
            if not valid:
                return

    def _get_daily(self):
        """get daily refresh values"""
        total_videos = self._get_total_hits("ta_video")
        video_daily = ceil(total_videos / self.interval * self.MULTIPLY)
        if video_daily >= 10000:
            video_daily = 9999

        total_channels = self._get_total_hits("ta_channel")
        channel_daily = ceil(total_channels / self.interval * self.MULTIPLY)
        total_playlists = self._get_total_hits("ta_playlist")
        playlist_daily = ceil(total_playlists / self.interval * self.MULTIPLY)
        return (video_daily, channel_daily, playlist_daily)

    def _get_total_hits(self, index):
        """get total hits from index"""
        match_field = self.MATCH_FIELD[index]
        path = f"{index}/_search?filter_path=hits.total"
        data = {"query": {"match": {match_field: True}}}
        response, _ = ElasticWrap(path).post(data=data)
        total_hits = response["hits"]["total"]["value"]
        return total_hits

    def _get_unrated_vids(self):
        """get max 200 videos without rating if ryd integration is enabled"""
        data = {
            "size": 200,
            "query": {
                "bool": {
                    "must_not": [{"exists": {"field": "stats.average_rating"}}]
                }
            },
        }
        response, _ = ElasticWrap("ta_video/_search").get(data=data)

        missing_rating = [i["_id"] for i in response["hits"]["hits"]]
        self.all_youtube_ids = self.all_youtube_ids + missing_rating

    def _get_outdated_vids(self, size):
        """get daily videos to refresh"""
        now_lte = self.now - self.interval * 24 * 60 * 60
        must_list = [
            {"match": {"active": True}},
            {"range": {"vid_last_refresh": {"lte": now_lte}}},
        ]
        data = {
            "size": size,
            "query": {"bool": {"must": must_list}},
            "sort": [{"vid_last_refresh": {"order": "asc"}}],
            "_source": False,
        }
        response, _ = ElasticWrap("ta_video/_search").get(data=data)

        all_youtube_ids = [i["_id"] for i in response["hits"]["hits"]]
        return all_youtube_ids

    def _get_outdated_channels(self, size):
        """get daily channels to refresh"""
        now_lte = self.now - self.interval * 24 * 60 * 60
        must_list = [
            {"match": {"channel_active": True}},
            {"range": {"channel_last_refresh": {"lte": now_lte}}},
        ]
        data = {
            "size": size,
            "query": {"bool": {"must": must_list}},
            "sort": [{"channel_last_refresh": {"order": "asc"}}],
            "_source": False,
        }
        response, _ = ElasticWrap("ta_channel/_search").get(data=data)

        all_channel_ids = [i["_id"] for i in response["hits"]["hits"]]
        return all_channel_ids

    def _get_outdated_playlists(self, size):
        """get daily outdated playlists to refresh"""
        now_lte = self.now - self.interval * 24 * 60 * 60
        must_list = [
            {"match": {"playlist_active": True}},
            {"range": {"playlist_last_refresh": {"lte": now_lte}}},
        ]
        data = {
            "size": size,
            "query": {"bool": {"must": must_list}},
            "sort": [{"playlist_last_refresh": {"order": "asc"}}],
            "_source": False,
        }
        response, _ = ElasticWrap("ta_playlist/_search").get(data=data)

        all_playlist_ids = [i["_id"] for i in response["hits"]["hits"]]
        return all_playlist_ids

    def check_outdated(self):
        """add missing vids and channels"""
        video_daily, channel_daily, playlist_daily = self._get_daily()
        self.all_youtube_ids = self._get_outdated_vids(video_daily)
        self.all_channel_ids = self._get_outdated_channels(channel_daily)
        self.all_playlist_ids = self._get_outdated_playlists(playlist_daily)

        integrate_ryd = self.config["downloads"]["integrate_ryd"]
        if integrate_ryd:
            self._get_unrated_vids()

    @staticmethod
    def _reindex_single_video(youtube_id):
        """refresh data for single video"""
        video = YoutubeVideo(youtube_id)

        # read current state
        video.get_from_es()
        player = video.json_data["player"]
        date_downloaded = video.json_data["date_downloaded"]
        channel_dict = video.json_data["channel"]
        playlist = video.json_data.get("playlist")
        subtitles = video.json_data.get("subtitles")

        # get new
        video.build_json()
        if not video.youtube_meta:
            video.deactivate()
            return

        video.delete_subtitles(subtitles=subtitles)
        video.check_subtitles()

        # add back
        video.json_data["player"] = player
        video.json_data["date_downloaded"] = date_downloaded
        video.json_data["channel"] = channel_dict
        if playlist:
            video.json_data["playlist"] = playlist

        video.upload_to_es()

        thumb_handler = ThumbManager()
        thumb_handler.delete_vid_thumb(youtube_id)
        to_download = (youtube_id, video.json_data["vid_thumb_url"])
        thumb_handler.download_vid([to_download], notify=False)
        return

    @staticmethod
    def _reindex_single_channel(channel_id):
        """refresh channel data and sync to videos"""
        channel = YoutubeChannel(channel_id)
        channel.get_from_es()
        subscribed = channel.json_data["channel_subscribed"]
        overwrites = channel.json_data.get("channel_overwrites", False)
        channel.get_from_youtube()
        channel.json_data["channel_subscribed"] = subscribed
        if overwrites:
            channel.json_data["channel_overwrites"] = overwrites
        channel.upload_to_es()
        channel.sync_to_videos()

    @staticmethod
    def _reindex_single_playlist(playlist_id, all_indexed_ids):
        """refresh playlist data"""
        playlist = YoutubePlaylist(playlist_id)
        playlist.get_from_es()
        subscribed = playlist.json_data["playlist_subscribed"]
        playlist.all_youtube_ids = all_indexed_ids
        playlist.build_json(scrape=True)
        if not playlist.json_data:
            playlist.deactivate()
            return

        playlist.json_data["playlist_subscribed"] = subscribed
        playlist.upload_to_es()
        return

    def reindex(self):
        """reindex what's needed"""
        sleep_interval = self.config["downloads"]["sleep_interval"]
        # videos
        print(f"reindexing {len(self.all_youtube_ids)} videos")
        for youtube_id in self.all_youtube_ids:
            try:
                self._reindex_single_video(youtube_id)
            except FileNotFoundError:
                # handle channel name change here
                ChannelUrlFixer(youtube_id, self.config).run()
                self._reindex_single_video(youtube_id)
            if sleep_interval:
                sleep(sleep_interval)
        # channels
        print(f"reindexing {len(self.all_channel_ids)} channels")
        for channel_id in self.all_channel_ids:
            self._reindex_single_channel(channel_id)
            if sleep_interval:
                sleep(sleep_interval)
        # playlist
        print(f"reindexing {len(self.all_playlist_ids)} playlists")
        if self.all_playlist_ids:
            handler = PendingList()
            handler.get_download()
            handler.get_indexed()
            all_indexed_ids = [i["youtube_id"] for i in handler.all_videos]
            for playlist_id in self.all_playlist_ids:
                self._reindex_single_playlist(playlist_id, all_indexed_ids)
                if sleep_interval:
                    sleep(sleep_interval)


class ChannelUrlFixer:
    """fix not matching channel names in reindex"""

    def __init__(self, youtube_id, config):
        self.youtube_id = youtube_id
        self.config = config
        self.video = False

    def run(self):
        """check and run if needed"""
        print(f"{self.youtube_id}: failed to build channel path, try to fix.")
        video_path_is, video_folder_is = self.get_as_is()
        if not os.path.exists(video_path_is):
            print(f"giving up reindex, video in video: {self.video.json_data}")
            raise ValueError

        _, video_folder_should = self.get_as_should()

        if video_folder_is != video_folder_should:
            self.process(video_path_is)
        else:
            print(f"{self.youtube_id}: skip channel url fixer")

    def get_as_is(self):
        """get video object as is"""
        self.video = YoutubeVideo(self.youtube_id)
        self.video.get_from_es()
        video_path_is = os.path.join(
            self.config["application"]["videos"],
            self.video.json_data["media_url"],
        )
        video_folder_is = os.path.split(video_path_is)[0]

        return video_path_is, video_folder_is

    def get_as_should(self):
        """add fresh metadata from remote"""
        self.video.get_from_youtube()
        self.video.add_file_path()

        video_path_should = os.path.join(
            self.config["application"]["videos"],
            self.video.json_data["media_url"],
        )
        video_folder_should = os.path.split(video_path_should)[0]
        return video_path_should, video_folder_should

    def process(self, video_path_is):
        """fix filepath"""
        print(f"{self.youtube_id}: fixing channel rename.")
        cache_dir = self.config["application"]["cache_dir"]
        new_file_path = os.path.join(
            cache_dir, "download", self.youtube_id + ".mp4"
        )
        shutil.move(video_path_is, new_file_path, copy_function=shutil.copy)
        VideoDownloader().move_to_archive(self.video.json_data)
        self.video.update_media_url()
