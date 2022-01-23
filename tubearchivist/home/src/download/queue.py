"""
Functionality:
- handle download queue
- linked with ta_dowload index
"""

import json
import os
from datetime import datetime

import requests
import yt_dlp
from home.src.download.subscriptions import ChannelSubscription
from home.src.es.connect import IndexPaginate
from home.src.index.playlist import YoutubePlaylist
from home.src.ta.config import AppConfig
from home.src.ta.helper import DurationConverter, ignore_filelist
from home.src.ta.ta_redis import RedisArchivist


class PendingList:
    """manage the pending videos list"""

    CONFIG = AppConfig().config
    ES_URL = CONFIG["application"]["es_url"]
    ES_AUTH = CONFIG["application"]["es_auth"]
    VIDEOS = CONFIG["application"]["videos"]

    def __init__(self):
        self.all_channel_ids = False
        self.all_downloaded = False
        self.missing_from_playlists = []

    def parse_url_list(self, youtube_ids):
        """extract youtube ids from list"""
        missing_videos = []
        for entry in youtube_ids:
            # notify
            mess_dict = {
                "status": "message:add",
                "level": "info",
                "title": "Adding to download queue.",
                "message": "Extracting lists",
            }
            RedisArchivist().set_message("message:add", mess_dict)
            # extract
            url = entry["url"]
            url_type = entry["type"]
            if url_type == "video":
                missing_videos.append(url)
            elif url_type == "channel":
                video_results = ChannelSubscription().get_last_youtube_videos(
                    url, limit=False
                )
                youtube_ids = [i[0] for i in video_results]
                missing_videos = missing_videos + youtube_ids
            elif url_type == "playlist":
                self.missing_from_playlists.append(entry)
                playlist = YoutubePlaylist(url)
                playlist.build_json()
                video_results = playlist.json_data.get("playlist_entries")
                youtube_ids = [i["youtube_id"] for i in video_results]
                missing_videos = missing_videos + youtube_ids

        return missing_videos

    def add_to_pending(self, missing_videos, ignore=False):
        """build the bulk json data from pending"""
        # check if channel is indexed
        channel_handler = ChannelSubscription()
        all_indexed = channel_handler.get_channels(subscribed_only=False)
        self.all_channel_ids = [i["channel_id"] for i in all_indexed]
        # check if already there
        self.all_downloaded = self.get_all_downloaded()

        bulk_list, all_videos_added = self.build_bulk(missing_videos, ignore)
        # add last newline
        bulk_list.append("\n")
        query_str = "\n".join(bulk_list)
        headers = {"Content-type": "application/x-ndjson"}
        url = self.ES_URL + "/_bulk"
        request = requests.post(
            url, data=query_str, headers=headers, auth=self.ES_AUTH
        )
        if not request.ok:
            print(request)
            raise ValueError("failed to add video to download queue")

        return all_videos_added

    def build_bulk(self, missing_videos, ignore=False):
        """build the bulk lists"""
        bulk_list = []
        all_videos_added = []

        for idx, youtube_id in enumerate(missing_videos):
            # check if already downloaded
            if youtube_id in self.all_downloaded:
                continue

            video = self.get_youtube_details(youtube_id)
            # skip on download error
            if not video:
                continue

            channel_indexed = video["channel_id"] in self.all_channel_ids
            video["channel_indexed"] = channel_indexed
            if ignore:
                video["status"] = "ignore"
            else:
                video["status"] = "pending"
            action = {"create": {"_id": youtube_id, "_index": "ta_download"}}
            bulk_list.append(json.dumps(action))
            bulk_list.append(json.dumps(video))
            all_videos_added.append((youtube_id, video["vid_thumb_url"]))
            # notify
            progress = f"{idx + 1}/{len(missing_videos)}"
            mess_dict = {
                "status": "message:add",
                "level": "info",
                "title": "Adding new videos to download queue.",
                "message": "Progress: " + progress,
            }
            if idx + 1 == len(missing_videos):
                RedisArchivist().set_message(
                    "message:add", mess_dict, expire=4
                )
            else:
                RedisArchivist().set_message("message:add", mess_dict)
            if idx + 1 % 25 == 0:
                print("adding to queue progress: " + progress)

        return bulk_list, all_videos_added

    @staticmethod
    def get_youtube_details(youtube_id):
        """get details from youtubedl for single pending video"""
        obs = {
            "default_search": "ytsearch",
            "quiet": True,
            "check_formats": "selected",
            "noplaylist": True,
            "writethumbnail": True,
            "simulate": True,
        }
        try:
            vid = yt_dlp.YoutubeDL(obs).extract_info(youtube_id)
        except yt_dlp.utils.DownloadError:
            print("failed to extract info for: " + youtube_id)
            return False
        # stop if video is streaming live now
        if vid["is_live"]:
            return False
        # parse response
        seconds = vid["duration"]
        duration_str = DurationConverter.get_str(seconds)
        if duration_str == "NA":
            print(f"skip extracting duration for: {youtube_id}")
        upload_date = vid["upload_date"]
        upload_dt = datetime.strptime(upload_date, "%Y%m%d")
        published = upload_dt.strftime("%Y-%m-%d")
        # build dict
        youtube_details = {
            "youtube_id": youtube_id,
            "channel_name": vid["channel"],
            "vid_thumb_url": vid["thumbnail"],
            "title": vid["title"],
            "channel_id": vid["channel_id"],
            "duration": duration_str,
            "published": published,
            "timestamp": int(datetime.now().strftime("%s")),
        }
        return youtube_details

    @staticmethod
    def get_all_pending():
        """get a list of all pending videos in ta_download"""
        data = {
            "query": {"match_all": {}},
            "sort": [{"timestamp": {"order": "asc"}}],
        }
        all_results = IndexPaginate("ta_download", data).get_results()

        all_pending = []
        all_ignore = []

        for result in all_results:
            if result["status"] == "pending":
                all_pending.append(result)
            elif result["status"] == "ignore":
                all_ignore.append(result)

        return all_pending, all_ignore

    @staticmethod
    def get_all_indexed():
        """get a list of all videos indexed"""

        data = {
            "query": {"match_all": {}},
            "sort": [{"published": {"order": "desc"}}],
        }
        all_indexed = IndexPaginate("ta_video", data).get_results()

        return all_indexed

    def get_all_downloaded(self):
        """get a list of all videos in archive"""
        channel_folders = os.listdir(self.VIDEOS)
        all_channel_folders = ignore_filelist(channel_folders)
        all_downloaded = []
        for channel_folder in all_channel_folders:
            channel_path = os.path.join(self.VIDEOS, channel_folder)
            videos = os.listdir(channel_path)
            all_videos = ignore_filelist(videos)
            youtube_vids = [i[9:20] for i in all_videos]
            for youtube_id in youtube_vids:
                all_downloaded.append(youtube_id)
        return all_downloaded

    def delete_from_pending(self, youtube_id):
        """delete the youtube_id from ta_download"""
        url = f"{self.ES_URL}/ta_download/_doc/{youtube_id}"
        response = requests.delete(url, auth=self.ES_AUTH)
        if not response.ok:
            print(response.text)

    def delete_pending(self, status):
        """delete download queue based on status value"""
        data = {"query": {"term": {"status": {"value": status}}}}
        payload = json.dumps(data)
        url = self.ES_URL + "/ta_download/_delete_by_query"
        headers = {"Content-type": "application/json"}
        response = requests.post(
            url, data=payload, headers=headers, auth=self.ES_AUTH
        )
        if not response.ok:
            print(response.text)

    def ignore_from_pending(self, ignore_list):
        """build the bulk query string"""

        stamp = int(datetime.now().strftime("%s"))
        bulk_list = []

        for youtube_id in ignore_list:
            action = {"update": {"_id": youtube_id, "_index": "ta_download"}}
            source = {"doc": {"status": "ignore", "timestamp": stamp}}
            bulk_list.append(json.dumps(action))
            bulk_list.append(json.dumps(source))

        # add last newline
        bulk_list.append("\n")
        query_str = "\n".join(bulk_list)

        headers = {"Content-type": "application/x-ndjson"}
        url = self.ES_URL + "/_bulk"
        request = requests.post(
            url, data=query_str, headers=headers, auth=self.ES_AUTH
        )
        if not request.ok:
            print(request)
            raise ValueError("failed to set video to ignore")
