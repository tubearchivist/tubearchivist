"""
functionality:
- periodically refresh documents
- index and update in es
"""

import json
from datetime import datetime
from math import ceil
from time import sleep

import requests
from home.src.download.queue import PendingList
from home.src.download.thumbnails import ThumbManager
from home.src.index.channel import YoutubeChannel
from home.src.index.playlist import YoutubePlaylist
from home.src.index.video import YoutubeVideo
from home.src.ta.config import AppConfig
from home.src.ta.helper import get_total_hits


class Reindex:
    """check for outdated documents and refresh data from youtube"""

    def __init__(self):
        # config
        config = AppConfig().config
        self.sleep_interval = config["downloads"]["sleep_interval"]
        self.es_url = config["application"]["es_url"]
        self.es_auth = config["application"]["es_auth"]
        self.refresh_interval = config["scheduler"]["check_reindex_days"]
        self.integrate_ryd = config["downloads"]["integrate_ryd"]
        # scan
        self.all_youtube_ids = False
        self.all_channel_ids = False
        self.all_playlist_ids = False

    def get_daily(self):
        """get daily refresh values"""
        total_videos = get_total_hits(
            "ta_video", self.es_url, self.es_auth, "active"
        )
        video_daily = ceil(total_videos / self.refresh_interval * 1.2)
        total_channels = get_total_hits(
            "ta_channel", self.es_url, self.es_auth, "channel_active"
        )
        channel_daily = ceil(total_channels / self.refresh_interval * 1.2)
        total_playlists = get_total_hits(
            "ta_playlist", self.es_url, self.es_auth, "playlist_active"
        )
        playlist_daily = ceil(total_playlists / self.refresh_interval * 1.2)
        return (video_daily, channel_daily, playlist_daily)

    def get_outdated_vids(self, size):
        """get daily videos to refresh"""
        headers = {"Content-type": "application/json"}
        now = int(datetime.now().strftime("%s"))
        now_lte = now - self.refresh_interval * 24 * 60 * 60
        data = {
            "size": size,
            "query": {
                "bool": {
                    "must": [
                        {"match": {"active": True}},
                        {"range": {"vid_last_refresh": {"lte": now_lte}}},
                    ]
                }
            },
            "sort": [{"vid_last_refresh": {"order": "asc"}}],
            "_source": False,
        }
        query_str = json.dumps(data)
        url = self.es_url + "/ta_video/_search"
        response = requests.get(
            url, data=query_str, headers=headers, auth=self.es_auth
        )
        if not response.ok:
            print(response.text)
        response_dict = json.loads(response.text)
        all_youtube_ids = [i["_id"] for i in response_dict["hits"]["hits"]]
        return all_youtube_ids

    def get_unrated_vids(self):
        """get all videos without rating if ryd integration is enabled"""
        headers = {"Content-type": "application/json"}
        data = {
            "size": 200,
            "query": {
                "bool": {
                    "must_not": [{"exists": {"field": "stats.average_rating"}}]
                }
            },
        }
        query_str = json.dumps(data)
        url = self.es_url + "/ta_video/_search"
        response = requests.get(
            url, data=query_str, headers=headers, auth=self.es_auth
        )
        if not response.ok:
            print(response.text)
        response_dict = json.loads(response.text)
        missing_rating = [i["_id"] for i in response_dict["hits"]["hits"]]
        self.all_youtube_ids = self.all_youtube_ids + missing_rating

    def get_outdated_channels(self, size):
        """get daily channels to refresh"""
        headers = {"Content-type": "application/json"}
        now = int(datetime.now().strftime("%s"))
        now_lte = now - self.refresh_interval * 24 * 60 * 60
        data = {
            "size": size,
            "query": {
                "bool": {
                    "must": [
                        {"match": {"channel_active": True}},
                        {"range": {"channel_last_refresh": {"lte": now_lte}}},
                    ]
                }
            },
            "sort": [{"channel_last_refresh": {"order": "asc"}}],
            "_source": False,
        }
        query_str = json.dumps(data)
        url = self.es_url + "/ta_channel/_search"
        response = requests.get(
            url, data=query_str, headers=headers, auth=self.es_auth
        )
        if not response.ok:
            print(response.text)
        response_dict = json.loads(response.text)
        all_channel_ids = [i["_id"] for i in response_dict["hits"]["hits"]]
        return all_channel_ids

    def get_outdated_playlists(self, size):
        """get daily outdated playlists to refresh"""
        headers = {"Content-type": "application/json"}
        now = int(datetime.now().strftime("%s"))
        now_lte = now - self.refresh_interval * 24 * 60 * 60
        data = {
            "size": size,
            "query": {
                "bool": {
                    "must": [
                        {"match": {"playlist_active": True}},
                        {"range": {"playlist_last_refresh": {"lte": now_lte}}},
                    ]
                }
            },
            "sort": [{"playlist_last_refresh": {"order": "asc"}}],
            "_source": False,
        }
        query_str = json.dumps(data)
        url = self.es_url + "/ta_playlist/_search"
        response = requests.get(
            url, data=query_str, headers=headers, auth=self.es_auth
        )
        if not response.ok:
            print(response.text)
        response_dict = json.loads(response.text)
        all_playlist_ids = [i["_id"] for i in response_dict["hits"]["hits"]]
        return all_playlist_ids

    def check_outdated(self):
        """add missing vids and channels"""
        video_daily, channel_daily, playlist_daily = self.get_daily()
        self.all_youtube_ids = self.get_outdated_vids(video_daily)
        self.all_channel_ids = self.get_outdated_channels(channel_daily)
        self.all_playlist_ids = self.get_outdated_playlists(playlist_daily)
        if self.integrate_ryd:
            self.get_unrated_vids()

    @staticmethod
    def reindex_single_video(youtube_id):
        """refresh data for single video"""
        video = YoutubeVideo(youtube_id)

        # read current state
        video.get_from_es()
        player = video.json_data["player"]
        date_downloaded = video.json_data["date_downloaded"]
        channel_dict = video.json_data["channel"]
        playlist = video.json_data.get("playlist")

        # get new
        video.build_json()
        if not video.youtube_meta:
            video.deactivate()
            return

        video.delete_subtitles()
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
    def reindex_single_channel(channel_id):
        """refresh channel data and sync to videos"""
        channel = YoutubeChannel(channel_id)
        channel.get_from_es()
        subscribed = channel.json_data["channel_subscribed"]
        overwrites = channel.json_data["channel_overwrites"]
        channel.get_from_youtube()
        channel.json_data["channel_subscribed"] = subscribed
        channel.json_data["channel_overwrites"] = overwrites
        channel.upload_to_es()
        channel.sync_to_videos()

    @staticmethod
    def reindex_single_playlist(playlist_id, all_indexed_ids):
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
        # videos
        print(f"reindexing {len(self.all_youtube_ids)} videos")
        for youtube_id in self.all_youtube_ids:
            self.reindex_single_video(youtube_id)
            if self.sleep_interval:
                sleep(self.sleep_interval)
        # channels
        print(f"reindexing {len(self.all_channel_ids)} channels")
        for channel_id in self.all_channel_ids:
            self.reindex_single_channel(channel_id)
            if self.sleep_interval:
                sleep(self.sleep_interval)
        # playlist
        print(f"reindexing {len(self.all_playlist_ids)} playlists")
        if self.all_playlist_ids:
            handler = PendingList()
            handler.get_indexed()
            all_indexed_ids = [i["youtube_id"] for i in handler.all_videos]
            for playlist_id in self.all_playlist_ids:
                self.reindex_single_playlist(playlist_id, all_indexed_ids)
                if self.sleep_interval:
                    sleep(self.sleep_interval)
