"""
Functionality:
- handele the download queue
- manage subscriptions to channels
- downloading videos
"""

import json
import os
import shutil
from datetime import datetime
from time import sleep

import requests
import yt_dlp as youtube_dl
from home.src.config import AppConfig
from home.src.helper import (
    DurationConverter,
    RedisArchivist,
    RedisQueue,
    clean_string,
    ignore_filelist,
)
from home.src.index import (
    IndexPaginate,
    YoutubeChannel,
    YoutubePlaylist,
    index_new_video,
)


class PendingList:
    """manage the pending videos list"""

    CONFIG = AppConfig().config
    ES_URL = CONFIG["application"]["es_url"]
    ES_AUTH = CONFIG["application"]["es_auth"]
    VIDEOS = CONFIG["application"]["videos"]

    def __init__(self):
        self.all_channel_ids = False
        self.all_downloaded = False

    @staticmethod
    def parse_url_list(youtube_ids):
        """extract youtube ids from list"""
        missing_videos = []
        for entry in youtube_ids:
            # notify
            mess_dict = {
                "status": "pending",
                "level": "info",
                "title": "Adding to download queue.",
                "message": "Extracting lists",
            }
            RedisArchivist().set_message("progress:download", mess_dict)
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
                video_results = YoutubePlaylist(url).get_entries()
                youtube_ids = [i["youtube_id"] for i in video_results]
                missing_videos = missing_videos + youtube_ids

        return missing_videos

    def add_to_pending(self, missing_videos):
        """build the bulk json data from pending"""
        # check if channel is indexed
        channel_handler = ChannelSubscription()
        all_indexed = channel_handler.get_channels(subscribed_only=False)
        self.all_channel_ids = [i["channel_id"] for i in all_indexed]
        # check if already there
        self.all_downloaded = self.get_all_downloaded()

        bulk_list, all_videos_added = self.build_bulk(missing_videos)
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

        return all_videos_added

    def build_bulk(self, missing_videos):
        """build the bulk lists"""
        bulk_list = []
        all_videos_added = []
        counter = 1
        for youtube_id in missing_videos:
            # check if already downloaded
            if youtube_id in self.all_downloaded:
                continue

            video = self.get_youtube_details(youtube_id)
            # skip on download error
            if not video:
                continue

            channel_indexed = video["channel_id"] in self.all_channel_ids
            video["channel_indexed"] = channel_indexed
            thumb_url = video["vid_thumb_url"]
            video["status"] = "pending"
            action = {"create": {"_id": youtube_id, "_index": "ta_download"}}
            bulk_list.append(json.dumps(action))
            bulk_list.append(json.dumps(video))
            all_videos_added.append((youtube_id, thumb_url))
            # notify
            progress = f"{counter}/{len(missing_videos)}"
            mess_dict = {
                "status": "pending",
                "level": "info",
                "title": "Adding new videos to download queue.",
                "message": "Progress: " + progress,
            }
            RedisArchivist().set_message("progress:download", mess_dict)
            if counter % 25 == 0:
                print("adding to queue progress: " + progress)
            counter = counter + 1

        return bulk_list, all_videos_added

    @staticmethod
    def get_youtube_details(youtube_id):
        """get details from youtubedl for single pending video"""
        obs = {
            "default_search": "ytsearch",
            "quiet": True,
            "skip_download": True,
            "check_formats": True,
        }
        try:
            vid = youtube_dl.YoutubeDL(obs).extract_info(youtube_id)
        except youtube_dl.utils.DownloadError:
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
        mess_dict = {
            "status": "ignore",
            "level": "info",
            "title": "Added to ignore list",
            "message": "",
        }
        RedisArchivist().set_message("progress:download", mess_dict)
        if not request.ok:
            print(request)


class ChannelSubscription:
    """manage the list of channels subscribed"""

    def __init__(self):
        config = AppConfig().config
        self.es_url = config["application"]["es_url"]
        self.es_auth = config["application"]["es_auth"]
        self.channel_size = config["subscriptions"]["channel_size"]

    @staticmethod
    def get_channels(subscribed_only=True):
        """get a list of all channels subscribed to"""
        data = {
            "sort": [{"channel_name.keyword": {"order": "asc"}}],
        }
        if subscribed_only:
            data["query"] = {"term": {"channel_subscribed": {"value": True}}}
        else:
            data["query"] = {"match_all": {}}

        all_channels = IndexPaginate("ta_channel", data).get_results()

        return all_channels

    def get_last_youtube_videos(self, channel_id, limit=True):
        """get a list of last videos from channel"""
        url = f"https://www.youtube.com/channel/{channel_id}/videos"
        obs = {
            "default_search": "ytsearch",
            "quiet": True,
            "skip_download": True,
            "extract_flat": True,
        }
        if limit:
            obs["playlistend"] = self.channel_size
        chan = youtube_dl.YoutubeDL(obs).extract_info(url, download=False)
        last_videos = [(i["id"], i["title"]) for i in chan["entries"]]
        return last_videos

    def find_missing(self):
        """add missing videos from subscribed channels to pending"""
        all_channels = self.get_channels()
        pending_handler = PendingList()
        all_pending, all_ignore = pending_handler.get_all_pending()
        all_ids = [i["youtube_id"] for i in all_ignore + all_pending]
        all_downloaded = pending_handler.get_all_downloaded()
        to_ignore = all_ids + all_downloaded
        missing_videos = []
        counter = 1
        for channel in all_channels:
            channel_id = channel["channel_id"]
            last_videos = self.get_last_youtube_videos(channel_id)
            RedisArchivist().set_message(
                "progress:download",
                {
                    "status": "rescan",
                    "level": "info",
                    "title": "Scanning channels: Looking for new videos.",
                    "message": f"Progress: {counter}/{len(all_channels)}",
                },
            )
            for video in last_videos:
                youtube_id = video[0]
                if youtube_id not in to_ignore:
                    missing_videos.append(youtube_id)
            counter = counter + 1

        return missing_videos

    def change_subscribe(self, channel_id, channel_subscribed):
        """subscribe or unsubscribe from channel and update"""
        if not isinstance(channel_subscribed, bool):
            print("invalid status, should be bool")
            return
        headers = {"Content-type": "application/json"}
        channel_handler = YoutubeChannel(channel_id)
        channel_dict = channel_handler.channel_dict
        channel_dict["channel_subscribed"] = channel_subscribed
        if channel_subscribed:
            # handle subscribe
            url = self.es_url + "/ta_channel/_doc/" + channel_id
            payload = json.dumps(channel_dict)
            print(channel_dict)
        else:
            url = self.es_url + "/ta_channel/_update/" + channel_id
            payload = json.dumps({"doc": channel_dict})
        # update channel
        request = requests.post(
            url, data=payload, headers=headers, auth=self.es_auth
        )
        if not request.ok:
            print(request.text)
        # sync to videos
        channel_handler.sync_to_videos()
        if channel_handler.source == "scraped":
            channel_handler.get_channel_art()


class PlaylistSubscription:
    """manage the playlist download functionality"""

    def __init__(self):
        config = AppConfig().config
        self.es_url = config["application"]["es_url"]
        self.es_auth = config["application"]["es_auth"]
        self.channel_size = config["subscriptions"]["channel_size"]

    @staticmethod
    def get_playlists(subscribed_only=True):
        """get a list of all playlists"""
        data = {
            "sort": [{"playlist_channel.keyword": {"order": "desc"}}],
        }
        if subscribed_only:
            data["query"] = {"term": {"playlist_subscribed": {"value": True}}}
        else:
            data["query"] = {"match_all": {}}

        all_playlists = IndexPaginate("ta_playlist", data).get_results()

        return all_playlists

    def change_subscribe(self, playlist_id, subscribe_status):
        """change the subscribe status of a playlist"""
        playlist_handler = YoutubePlaylist(playlist_id)
        playlist_handler.get_playlist_dict()
        subed_now = playlist_handler.playlist_dict["playlist_subscribed"]

        if subed_now == subscribe_status:
            # status already as expected, do nothing
            return False

        # update subscribed status
        print(f"changing status of {playlist_id} to {subscribe_status}")
        headers = {"Content-type": "application/json"}
        url = f"{self.es_url}/ta_playlist/_update/{playlist_id}"
        payload = json.dumps(
            {"doc": {"playlist_subscribed": subscribe_status}}
        )
        response = requests.post(
            url, data=payload, headers=headers, auth=self.es_auth
        )
        if not response.ok:
            print(response.text)

        return True


class VideoDownloader:
    """
    handle the video download functionality
    if not initiated with list, take from queue
    """

    def __init__(self, youtube_id_list=False):
        self.youtube_id_list = youtube_id_list
        self.config = AppConfig().config

    def run_queue(self):
        """setup download queue in redis loop until no more items"""
        queue = RedisQueue("dl_queue")

        limit_queue = self.config["downloads"]["limit_count"]
        if limit_queue:
            queue.trim(limit_queue - 1)

        while True:
            youtube_id = queue.get_next()
            if not youtube_id:
                break

            try:
                self.dl_single_vid(youtube_id)
            except youtube_dl.utils.DownloadError:
                print("failed to download " + youtube_id)
                continue
            vid_dict = index_new_video(youtube_id)
            self.move_to_archive(vid_dict)
            self.delete_from_pending(youtube_id)

    @staticmethod
    def add_pending():
        """add pending videos to download queue"""
        all_pending, _ = PendingList().get_all_pending()
        to_add = [i["youtube_id"] for i in all_pending]
        if not to_add:
            # there is nothing pending
            print("download queue is empty")
            mess_dict = {
                "status": "downloading",
                "level": "error",
                "title": "Download queue is empty",
                "message": "",
            }
            RedisArchivist().set_message("progress:download", mess_dict)
            return

        queue = RedisQueue("dl_queue")
        queue.add_list(to_add)

    @staticmethod
    def progress_hook(response):
        """process the progress_hooks from youtube_dl"""
        # title
        filename = response["filename"][12:].replace("_", " ")
        title = "Downloading: " + os.path.split(filename)[-1]
        # message
        try:
            percent = response["_percent_str"]
            size = response["_total_bytes_str"]
            speed = response["_speed_str"]
            eta = response["_eta_str"]
            message = f"{percent} of {size} at {speed} - time left: {eta}"
        except KeyError:
            message = ""
        mess_dict = {
            "status": "downloading",
            "level": "info",
            "title": title,
            "message": message,
        }
        RedisArchivist().set_message("progress:download", mess_dict)

    def build_obs(self):
        """build obs dictionary for yt-dlp"""
        obs = {
            "default_search": "ytsearch",
            "merge_output_format": "mp4",
            "restrictfilenames": True,
            "outtmpl": (
                self.config["application"]["cache_dir"]
                + "/download/"
                + self.config["application"]["file_template"]
            ),
            "progress_hooks": [self.progress_hook],
            "noprogress": True,
            "quiet": True,
            "continuedl": True,
            "retries": 3,
            "writethumbnail": False,
        }
        if self.config["downloads"]["format"]:
            obs["format"] = self.config["downloads"]["format"]
        if self.config["downloads"]["limit_speed"]:
            obs["ratelimit"] = self.config["downloads"]["limit_speed"] * 1024

        throttle = self.config["downloads"]["throttledratelimit"]
        if throttle:
            obs["throttledratelimit"] = throttle * 1024

        external = False
        if external:
            obs["external_downloader"] = "aria2c"

        postprocessors = []

        if self.config["downloads"]["add_metadata"]:
            postprocessors.append(
                {
                    "key": "FFmpegMetadata",
                    "add_chapters": True,
                    "add_metadata": True,
                }
            )

        if self.config["downloads"]["add_thumbnail"]:
            postprocessors.append(
                {
                    "key": "EmbedThumbnail",
                    "already_have_thumbnail": True,
                }
            )
            obs["writethumbnail"] = True

        obs["postprocessors"] = postprocessors

        return obs

    def dl_single_vid(self, youtube_id):
        """download single video"""
        dl_cache = self.config["application"]["cache_dir"] + "/download/"
        obs = self.build_obs()

        # check if already in cache to continue from there
        all_cached = ignore_filelist(os.listdir(dl_cache))
        for file_name in all_cached:
            if youtube_id in file_name:
                obs["outtmpl"] = os.path.join(dl_cache, file_name)
        with youtube_dl.YoutubeDL(obs) as ydl:
            try:
                ydl.download([youtube_id])
            except youtube_dl.utils.DownloadError:
                print("retry failed download: " + youtube_id)
                sleep(10)
                ydl.download([youtube_id])

        if obs["writethumbnail"]:
            # webp files don't get cleaned up automatically
            all_cached = ignore_filelist(os.listdir(dl_cache))
            to_clean = [i for i in all_cached if not i.endswith(".mp4")]
            for file_name in to_clean:
                file_path = os.path.join(dl_cache, file_name)
                os.remove(file_path)

    def move_to_archive(self, vid_dict):
        """move downloaded video from cache to archive"""
        videos = self.config["application"]["videos"]
        host_uid = self.config["application"]["HOST_UID"]
        host_gid = self.config["application"]["HOST_GID"]
        channel_name = clean_string(vid_dict["channel"]["channel_name"])
        # make archive folder with correct permissions
        new_folder = os.path.join(videos, channel_name)
        if not os.path.exists(new_folder):
            os.makedirs(new_folder)
            if host_uid and host_gid:
                os.chown(new_folder, host_uid, host_gid)
        # find real filename
        cache_dir = self.config["application"]["cache_dir"]
        all_cached = ignore_filelist(os.listdir(cache_dir + "/download/"))
        for file_str in all_cached:
            if vid_dict["youtube_id"] in file_str:
                old_file = file_str
        old_file_path = os.path.join(cache_dir, "download", old_file)
        new_file_path = os.path.join(videos, vid_dict["media_url"])
        # move media file and fix permission
        shutil.move(old_file_path, new_file_path)
        if host_uid and host_gid:
            os.chown(new_file_path, host_uid, host_gid)

    def delete_from_pending(self, youtube_id):
        """delete downloaded video from pending index if its there"""
        es_url = self.config["application"]["es_url"]
        es_auth = self.config["application"]["es_auth"]
        url = f"{es_url}/ta_download/_doc/{youtube_id}"
        response = requests.delete(url, auth=es_auth)
        if not response.ok and not response.status_code == 404:
            print(response.text)
