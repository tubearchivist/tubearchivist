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
from home.src.index import YoutubeChannel, index_new_video


class PendingList:
    """manage the pending videos list"""

    CONFIG = AppConfig().config
    ES_URL = CONFIG["application"]["es_url"]
    VIDEOS = CONFIG["application"]["videos"]

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
                youtube_ids = ChannelSubscription().get_last_youtube_videos(
                    url, limit=False
                )
                missing_videos = missing_videos + youtube_ids
            elif url_type == "playlist":
                youtube_ids = playlist_extractor(url)
                missing_videos = missing_videos + youtube_ids

        return missing_videos

    def add_to_pending(self, missing_videos):
        """build the bulk json data from pending"""
        # check if channel is indexed
        channel_handler = ChannelSubscription()
        all_indexed = channel_handler.get_channels(subscribed_only=False)
        all_channel_ids = [i["channel_id"] for i in all_indexed]
        # check if already there
        all_downloaded = self.get_all_downloaded()
        # loop
        bulk_list = []
        all_videos_added = []
        for video in missing_videos:
            if isinstance(video, str):
                youtube_id = video
            elif isinstance(video, tuple):
                youtube_id = video[0]
            if youtube_id in all_downloaded:
                # skip already downloaded
                continue
            video = self.get_youtube_details(youtube_id)
            # skip on download error
            if not video:
                continue

            if video["channel_id"] in all_channel_ids:
                video["channel_indexed"] = True
            else:
                video["channel_indexed"] = False
            thumb_url = video["vid_thumb_url"]
            video["status"] = "pending"
            action = {"create": {"_id": youtube_id, "_index": "ta_download"}}
            bulk_list.append(json.dumps(action))
            bulk_list.append(json.dumps(video))
            all_videos_added.append((youtube_id, thumb_url))
            # notify
            mess_dict = {
                "status": "pending",
                "level": "info",
                "title": "Adding to download queue.",
                "message": "Processing IDs...",
            }
            RedisArchivist().set_message("progress:download", mess_dict)
        # add last newline
        bulk_list.append("\n")
        query_str = "\n".join(bulk_list)
        headers = {"Content-type": "application/x-ndjson"}
        url = self.ES_URL + "/_bulk"
        request = requests.post(url, data=query_str, headers=headers)
        if not request.ok:
            print(request)

        return all_videos_added

    @staticmethod
    def get_youtube_details(youtube_id):
        """get details from youtubedl for single pending video"""
        obs = {
            "default_search": "ytsearch",
            "quiet": True,
            "skip_download": True,
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

    def get_all_pending(self):
        """get a list of all pending videos in ta_download"""
        headers = {"Content-type": "application/json"}
        # get PIT ID
        url = self.ES_URL + "/ta_download/_pit?keep_alive=1m"
        response = requests.post(url)
        json_data = json.loads(response.text)
        pit_id = json_data["id"]
        # query
        data = {
            "size": 50,
            "query": {"match_all": {}},
            "pit": {"id": pit_id, "keep_alive": "1m"},
            "sort": [{"timestamp": {"order": "asc"}}],
        }
        query_str = json.dumps(data)
        url = self.ES_URL + "/_search"
        all_pending = []
        all_ignore = []
        while True:
            response = requests.get(url, data=query_str, headers=headers)
            json_data = json.loads(response.text)
            all_hits = json_data["hits"]["hits"]
            if all_hits:
                for hit in all_hits:
                    status = hit["_source"]["status"]
                    if status == "pending":
                        all_pending.append(hit["_source"])
                    elif status == "ignore":
                        all_ignore.append(hit["_source"])
                    search_after = hit["sort"]
                # update search_after with last hit data
                data["search_after"] = search_after
                query_str = json.dumps(data)
            else:
                break
        # clean up PIT
        query_str = json.dumps({"id": pit_id})
        requests.delete(self.ES_URL + "/_pit", data=query_str, headers=headers)
        return all_pending, all_ignore

    def get_all_indexed(self):
        """get a list of all videos indexed"""
        headers = {"Content-type": "application/json"}
        # get PIT ID
        url = self.ES_URL + "/ta_video/_pit?keep_alive=1m"
        response = requests.post(url)
        json_data = json.loads(response.text)
        pit_id = json_data["id"]
        # query
        data = {
            "size": 500,
            "query": {"match_all": {}},
            "pit": {"id": pit_id, "keep_alive": "1m"},
            "sort": [{"published": {"order": "desc"}}],
        }
        query_str = json.dumps(data)
        url = self.ES_URL + "/_search"
        all_indexed = []
        while True:
            response = requests.get(url, data=query_str, headers=headers)
            json_data = json.loads(response.text)
            all_hits = json_data["hits"]["hits"]
            if all_hits:
                for hit in all_hits:
                    all_indexed.append(hit)
                    search_after = hit["sort"]
                # update search_after with last hit data
                data["search_after"] = search_after
                query_str = json.dumps(data)
            else:
                break
        # clean up PIT
        query_str = json.dumps({"id": pit_id})
        requests.delete(self.ES_URL + "/_pit", data=query_str, headers=headers)
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
        response = requests.delete(url)
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
        request = requests.post(url, data=query_str, headers=headers)
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
        self.channel_size = config["subscriptions"]["channel_size"]

    def get_channels(self, subscribed_only=True):
        """get a list of all channels subscribed to"""
        headers = {"Content-type": "application/json"}
        # get PIT ID
        url = self.es_url + "/ta_channel/_pit?keep_alive=1m"
        response = requests.post(url)
        json_data = json.loads(response.text)
        pit_id = json_data["id"]
        # query
        if subscribed_only:
            data = {
                "query": {"term": {"channel_subscribed": {"value": True}}},
                "size": 50,
                "pit": {"id": pit_id, "keep_alive": "1m"},
                "sort": [{"channel_name.keyword": {"order": "asc"}}],
            }
        else:
            data = {
                "query": {"match_all": {}},
                "size": 50,
                "pit": {"id": pit_id, "keep_alive": "1m"},
                "sort": [{"channel_name.keyword": {"order": "asc"}}],
            }
        query_str = json.dumps(data)
        url = self.es_url + "/_search"
        all_channels = []
        while True:
            response = requests.get(url, data=query_str, headers=headers)
            json_data = json.loads(response.text)
            all_hits = json_data["hits"]["hits"]
            if all_hits:
                for hit in all_hits:
                    source = hit["_source"]
                    search_after = hit["sort"]
                    all_channels.append(source)
                # update search_after with last hit data
                data["search_after"] = search_after
                query_str = json.dumps(data)
            else:
                break
        # clean up PIT
        query_str = json.dumps({"id": pit_id})
        requests.delete(self.es_url + "/_pit", data=query_str, headers=headers)
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
                    "title": "Rescanning: Looking for new videos.",
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
        request = requests.post(url, data=payload, headers=headers)
        if not request.ok:
            print(request.text)
        # sync to videos
        channel_handler.sync_to_videos()
        if channel_handler.source == "scraped":
            channel_handler.get_channel_art()


def playlist_extractor(playlist_id):
    """return youtube_ids from a playlist_id"""
    url = "https://www.youtube.com/playlist?list=" + playlist_id
    obs = {
        "default_search": "ytsearch",
        "quiet": True,
        "ignoreerrors": True,
        "skip_download": True,
        "extract_flat": True,
    }
    playlist = youtube_dl.YoutubeDL(obs).extract_info(url, download=False)
    playlist_vids = [(i["id"], i["title"]) for i in playlist["entries"]]
    return playlist_vids


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
        os.chown(new_file_path, host_uid, host_gid)

    def delete_from_pending(self, youtube_id):
        """delete downloaded video from pending index if its there"""
        es_url = self.config["application"]["es_url"]
        url = f"{es_url}/ta_download/_doc/{youtube_id}"
        response = requests.delete(url)
        if not response.ok and not response.status_code == 404:
            print(response.text)
