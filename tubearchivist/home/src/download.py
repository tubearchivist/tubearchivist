"""
Functionality:
- handele the download queue
- manage subscriptions to channels
- manage subscriptions to playlists
- downloading videos
"""

import json
import os
import shutil
from datetime import datetime
from time import sleep

import requests
import yt_dlp
from home.src.config import AppConfig
from home.src.es import IndexPaginate
from home.src.helper import (
    DurationConverter,
    RedisArchivist,
    RedisQueue,
    clean_string,
    ignore_filelist,
)
from home.src.index import (
    YoutubeChannel,
    YoutubePlaylist,
    YoutubeVideo,
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
        chan = yt_dlp.YoutubeDL(obs).extract_info(url, download=False)
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

        for idx, channel in enumerate(all_channels):
            channel_id = channel["channel_id"]
            last_videos = self.get_last_youtube_videos(channel_id)
            for video in last_videos:
                if video[0] not in to_ignore:
                    missing_videos.append(video[0])
            # notify
            message = {
                "status": "message:rescan",
                "level": "info",
                "title": "Scanning channels: Looking for new videos.",
                "message": f"Progress: {idx + 1}/{len(all_channels)}",
            }
            if idx + 1 == len(all_channels):
                RedisArchivist().set_message(
                    "message:rescan", message=message, expire=4
                )
            else:
                RedisArchivist().set_message("message:rescan", message=message)

        return missing_videos

    @staticmethod
    def change_subscribe(channel_id, channel_subscribed):
        """subscribe or unsubscribe from channel and update"""
        channel = YoutubeChannel(channel_id)
        channel.build_json()
        channel.json_data["channel_subscribed"] = channel_subscribed
        channel.upload_to_es()
        channel.sync_to_videos()


class PlaylistSubscription:
    """manage the playlist download functionality"""

    def __init__(self):
        self.config = AppConfig().config

    @staticmethod
    def get_playlists(subscribed_only=True):
        """get a list of all active playlists"""
        data = {
            "sort": [{"playlist_channel.keyword": {"order": "desc"}}],
        }
        data["query"] = {
            "bool": {"must": [{"term": {"playlist_active": {"value": True}}}]}
        }
        if subscribed_only:
            data["query"]["bool"]["must"].append(
                {"term": {"playlist_subscribed": {"value": True}}}
            )

        all_playlists = IndexPaginate("ta_playlist", data).get_results()

        return all_playlists

    def process_url_str(self, new_playlists, subscribed=True):
        """process playlist subscribe form url_str"""
        all_indexed = PendingList().get_all_indexed()
        all_youtube_ids = [i["youtube_id"] for i in all_indexed]

        new_thumbs = []
        for idx, playlist in enumerate(new_playlists):
            url_type = playlist["type"]
            playlist_id = playlist["url"]
            if not url_type == "playlist":
                print(f"{playlist_id} not a playlist, skipping...")
                continue

            playlist_h = YoutubePlaylist(playlist_id)
            playlist_h.all_youtube_ids = all_youtube_ids
            playlist_h.build_json()
            playlist_h.json_data["playlist_subscribed"] = subscribed
            playlist_h.upload_to_es()
            playlist_h.add_vids_to_playlist()
            self.channel_validate(playlist_h.json_data["playlist_channel_id"])
            thumb = playlist_h.json_data["playlist_thumbnail"]
            new_thumbs.append((playlist_id, thumb))
            # notify
            message = {
                "status": "message:subplaylist",
                "level": "info",
                "title": "Subscribing to Playlists",
                "message": f"Processing {idx + 1} of {len(new_playlists)}",
            }
            RedisArchivist().set_message(
                "message:subplaylist", message=message
            )

        return new_thumbs

    @staticmethod
    def channel_validate(channel_id):
        """make sure channel of playlist is there"""
        channel = YoutubeChannel(channel_id)
        channel.build_json()

    @staticmethod
    def change_subscribe(playlist_id, subscribe_status):
        """change the subscribe status of a playlist"""
        playlist = YoutubePlaylist(playlist_id)
        playlist.build_json()
        playlist.json_data["playlist_subscribed"] = subscribe_status
        playlist.upload_to_es()

    @staticmethod
    def get_to_ignore():
        """get all youtube_ids already downloaded or ignored"""
        pending_handler = PendingList()
        all_pending, all_ignore = pending_handler.get_all_pending()
        all_ids = [i["youtube_id"] for i in all_ignore + all_pending]
        all_downloaded = pending_handler.get_all_downloaded()
        to_ignore = all_ids + all_downloaded
        return to_ignore

    def find_missing(self):
        """find videos in subscribed playlists not downloaded yet"""
        all_playlists = [i["playlist_id"] for i in self.get_playlists()]
        to_ignore = self.get_to_ignore()

        missing_videos = []
        for idx, playlist_id in enumerate(all_playlists):
            size_limit = self.config["subscriptions"]["channel_size"]
            playlist = YoutubePlaylist(playlist_id)
            playlist.update_playlist()
            if not playlist:
                playlist.deactivate()
                continue

            playlist_entries = playlist.json_data["playlist_entries"]
            if size_limit:
                del playlist_entries[size_limit:]

            all_missing = [i for i in playlist_entries if not i["downloaded"]]

            message = {
                "status": "message:rescan",
                "level": "info",
                "title": "Scanning playlists: Looking for new videos.",
                "message": f"Progress: {idx + 1}/{len(all_playlists)}",
            }
            RedisArchivist().set_message("message:rescan", message=message)

            for video in all_missing:
                youtube_id = video["youtube_id"]
                if youtube_id not in to_ignore:
                    missing_videos.append(youtube_id)

        return missing_videos


class VideoDownloader:
    """
    handle the video download functionality
    if not initiated with list, take from queue
    """

    def __init__(self, youtube_id_list=False):
        self.youtube_id_list = youtube_id_list
        self.config = AppConfig().config
        self.channels = set()

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
            except yt_dlp.utils.DownloadError:
                print("failed to download " + youtube_id)
                continue
            vid_dict = index_new_video(youtube_id)
            self.channels.add(vid_dict["channel"]["channel_id"])
            self.move_to_archive(vid_dict)
            self.delete_from_pending(youtube_id)

        autodelete_days = self.config["downloads"]["autodelete_days"]
        if autodelete_days:
            print(f"auto delete older than {autodelete_days} days")
            self.auto_delete_watched(autodelete_days)

    @staticmethod
    def add_pending():
        """add pending videos to download queue"""
        mess_dict = {
            "status": "message:download",
            "level": "info",
            "title": "Looking for videos to download",
            "message": "Scanning your download queue.",
        }
        RedisArchivist().set_message("message:download", mess_dict)
        all_pending, _ = PendingList().get_all_pending()
        to_add = [i["youtube_id"] for i in all_pending]
        if not to_add:
            # there is nothing pending
            print("download queue is empty")
            mess_dict = {
                "status": "message:download",
                "level": "error",
                "title": "Download queue is empty",
                "message": "Add some videos to the queue first.",
            }
            RedisArchivist().set_message("message:download", mess_dict)
            return

        queue = RedisQueue("dl_queue")
        queue.add_list(to_add)

    @staticmethod
    def progress_hook(response):
        """process the progress_hooks from yt_dlp"""
        # title
        path = os.path.split(response["filename"])[-1][12:]
        filename = os.path.splitext(os.path.splitext(path)[0])[0]
        filename_clean = filename.replace("_", " ")
        title = "Downloading: " + filename_clean
        # message
        try:
            percent = response["_percent_str"]
            size = response["_total_bytes_str"]
            speed = response["_speed_str"]
            eta = response["_eta_str"]
            message = f"{percent} of {size} at {speed} - time left: {eta}"
        except KeyError:
            message = "processing"
        mess_dict = {
            "status": "message:download",
            "level": "info",
            "title": title,
            "message": message,
        }
        RedisArchivist().set_message("message:download", mess_dict)

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
            "noplaylist": True,
            "check_formats": "selected",
        }
        if self.config["downloads"]["format"]:
            obs["format"] = self.config["downloads"]["format"]
        if self.config["downloads"]["limit_speed"]:
            obs["ratelimit"] = self.config["downloads"]["limit_speed"] * 1024

        throttle = self.config["downloads"]["throttledratelimit"]
        if throttle:
            obs["throttledratelimit"] = throttle * 1024

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
        with yt_dlp.YoutubeDL(obs) as ydl:
            try:
                ydl.download([youtube_id])
            except yt_dlp.utils.DownloadError:
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

    def add_subscribed_channels(self):
        """add all channels subscribed to refresh"""
        all_subscribed = PlaylistSubscription().get_playlists()
        if not all_subscribed:
            return

        channel_ids = [i["playlist_channel_id"] for i in all_subscribed]
        for channel_id in channel_ids:
            self.channels.add(channel_id)

        return

    def validate_playlists(self):
        """look for playlist needing to update"""
        print("sync playlists")
        self.add_subscribed_channels()
        all_indexed = PendingList().get_all_indexed()
        all_youtube_ids = [i["youtube_id"] for i in all_indexed]
        for id_c, channel_id in enumerate(self.channels):
            playlists = YoutubeChannel(channel_id).get_indexed_playlists()
            all_playlist_ids = [i["playlist_id"] for i in playlists]
            for id_p, playlist_id in enumerate(all_playlist_ids):
                playlist = YoutubePlaylist(playlist_id)
                playlist.all_youtube_ids = all_youtube_ids
                playlist.build_json(scrape=True)
                if not playlist.json_data:
                    playlist.deactivate()

                playlist.add_vids_to_playlist()
                playlist.upload_to_es()

                # notify
                title = (
                    "Processing playlists for channels: "
                    + f"{id_c + 1}/{len(self.channels)}"
                )
                message = f"Progress: {id_p + 1}/{len(all_playlist_ids)}"
                mess_dict = {
                    "status": "message:download",
                    "level": "info",
                    "title": title,
                    "message": message,
                }
                if id_p + 1 == len(all_playlist_ids):
                    RedisArchivist().set_message(
                        "message:download", mess_dict, expire=4
                    )
                else:
                    RedisArchivist().set_message("message:download", mess_dict)

    @staticmethod
    def auto_delete_watched(autodelete_days):
        """delete watched videos after x days"""
        now = int(datetime.now().strftime("%s"))
        now_lte = now - autodelete_days * 24 * 60 * 60
        data = {
            "query": {"range": {"player.watched_date": {"lte": now_lte}}},
            "sort": [{"player.watched_date": {"order": "asc"}}],
        }
        all_to_delete = IndexPaginate("ta_video", data).get_results()
        all_youtube_ids = [i["youtube_id"] for i in all_to_delete]
        if not all_youtube_ids:
            return

        for youtube_id in all_youtube_ids:
            print(f"autodelete {youtube_id}")
            YoutubeVideo(youtube_id).delete_media_file()

        print("add deleted to ignore list")
        pending_handler = PendingList()
        pending_handler.add_to_pending(all_youtube_ids, ignore=True)
