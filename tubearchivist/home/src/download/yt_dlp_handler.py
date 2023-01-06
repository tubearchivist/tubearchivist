"""
functionality:
- handle yt_dlp
- build options and post processor
- download video files
- move to archive
"""

import json
import os
import shutil
from datetime import datetime

from home.src.download.queue import PendingList
from home.src.download.subscriptions import PlaylistSubscription
from home.src.download.yt_dlp_base import CookieHandler, YtWrap
from home.src.es.connect import ElasticWrap, IndexPaginate
from home.src.index.channel import YoutubeChannel
from home.src.index.comments import CommentList
from home.src.index.playlist import YoutubePlaylist
from home.src.index.video import YoutubeVideo, index_new_video
from home.src.index.video_constants import VideoTypeEnum
from home.src.ta.config import AppConfig
from home.src.ta.helper import clean_string, ignore_filelist
from home.src.ta.ta_redis import RedisArchivist, RedisQueue


class DownloadPostProcess:
    """handle task to run after download queue finishes"""

    def __init__(self, download):
        self.download = download
        self.now = int(datetime.now().timestamp())
        self.pending = False

    def run(self):
        """run all functions"""
        self.pending = PendingList()
        self.pending.get_download()
        self.pending.get_channels()
        self.pending.get_indexed()
        self.auto_delete_all()
        self.auto_delete_overwrites()
        self.validate_playlists()
        self.get_comments()

    def auto_delete_all(self):
        """handle auto delete"""
        autodelete_days = self.download.config["downloads"]["autodelete_days"]
        if not autodelete_days:
            return

        print(f"auto delete older than {autodelete_days} days")
        now_lte = self.now - autodelete_days * 24 * 60 * 60
        data = {
            "query": {"range": {"player.watched_date": {"lte": now_lte}}},
            "sort": [{"player.watched_date": {"order": "asc"}}],
        }
        self._auto_delete_watched(data)

    def auto_delete_overwrites(self):
        """handle per channel auto delete from overwrites"""
        for channel_id, value in self.pending.channel_overwrites.items():
            if "autodelete_days" in value:
                autodelete_days = value.get("autodelete_days")
                print(f"{channel_id}: delete older than {autodelete_days}d")
                now_lte = self.now - autodelete_days * 24 * 60 * 60
                must_list = [
                    {"range": {"player.watched_date": {"lte": now_lte}}},
                    {"term": {"channel.channel_id": {"value": channel_id}}},
                ]
                data = {
                    "query": {"bool": {"must": must_list}},
                    "sort": [{"player.watched_date": {"order": "desc"}}],
                }
                self._auto_delete_watched(data)

    @staticmethod
    def _auto_delete_watched(data):
        """delete watched videos after x days"""
        to_delete = IndexPaginate("ta_video", data).get_results()
        if not to_delete:
            return

        for video in to_delete:
            youtube_id = video["youtube_id"]
            print(f"{youtube_id}: auto delete video")
            YoutubeVideo(youtube_id).delete_media_file()

        print("add deleted to ignore list")
        vids = [{"type": "video", "url": i["youtube_id"]} for i in to_delete]
        pending = PendingList(youtube_ids=vids)
        pending.parse_url_list()
        pending.add_to_pending(status="ignore")

    def validate_playlists(self):
        """look for playlist needing to update"""
        for id_c, channel_id in enumerate(self.download.channels):
            channel = YoutubeChannel(channel_id)
            overwrites = self.pending.channel_overwrites.get(channel_id, False)
            if overwrites and overwrites.get("index_playlists"):
                # validate from remote
                channel.index_channel_playlists()
                continue

            # validate from local
            playlists = channel.get_indexed_playlists(active_only=True)
            all_channel_playlist = [i["playlist_id"] for i in playlists]
            self._validate_channel_playlist(all_channel_playlist, id_c)

    def _validate_channel_playlist(self, all_channel_playlist, id_c):
        """scan channel for playlist needing update"""
        all_youtube_ids = [i["youtube_id"] for i in self.pending.all_videos]
        for id_p, playlist_id in enumerate(all_channel_playlist):
            playlist = YoutubePlaylist(playlist_id)
            playlist.all_youtube_ids = all_youtube_ids
            playlist.build_json(scrape=True)
            if not playlist.json_data:
                playlist.deactivate()
                continue

            playlist.add_vids_to_playlist()
            playlist.upload_to_es()
            self._notify_playlist_progress(all_channel_playlist, id_c, id_p)

    def _notify_playlist_progress(self, all_channel_playlist, id_c, id_p):
        """notify to UI"""
        title = (
            "Processing playlists for channels: "
            + f"{id_c + 1}/{len(self.download.channels)}"
        )
        message = f"Progress: {id_p + 1}/{len(all_channel_playlist)}"
        key = "message:download"
        mess_dict = {
            "status": key,
            "level": "info",
            "title": title,
            "message": message,
        }
        if id_p + 1 == len(all_channel_playlist):
            expire = 4
        else:
            expire = True

        RedisArchivist().set_message(key, mess_dict, expire=expire)

    def get_comments(self):
        """get comments from youtube"""
        CommentList(self.download.videos).index(notify=True)


class VideoDownloader:
    """
    handle the video download functionality
    if not initiated with list, take from queue
    """

    MSG = "message:download"

    def __init__(self, youtube_id_list=False):
        self.obs = False
        self.video_overwrites = False
        self.youtube_id_list = youtube_id_list
        self.config = AppConfig().config
        self._build_obs()
        self.channels = set()
        self.videos = set()

    def run_queue(self):
        """setup download queue in redis loop until no more items"""
        self._setup_queue()

        queue = RedisQueue(queue_name="dl_queue")

        limit_queue = self.config["downloads"]["limit_count"]
        if limit_queue:
            queue.trim(limit_queue - 1)

        while True:
            youtube_data = queue.get_next()
            if not youtube_data:
                break

            try:
                youtube_data = json.loads(youtube_data)
            except json.JSONDecodeError:  # This many not be necessary
                continue

            youtube_id = youtube_data.get("youtube_id")

            tmp_vid_type = youtube_data.get(
                "vid_type", VideoTypeEnum.VIDEOS.value
            )
            video_type = VideoTypeEnum(tmp_vid_type)
            print(f"Downloading type: {video_type}")

            success = self._dl_single_vid(youtube_id)
            if not success:
                continue

            mess_dict = {
                "status": self.MSG,
                "level": "info",
                "title": "Indexing....",
                "message": "Add video metadata to index.",
            }
            RedisArchivist().set_message(self.MSG, mess_dict, expire=60)

            vid_dict = index_new_video(
                youtube_id,
                video_overwrites=self.video_overwrites,
                video_type=video_type,
            )
            self.channels.add(vid_dict["channel"]["channel_id"])
            self.videos.add(vid_dict["youtube_id"])
            mess_dict = {
                "status": self.MSG,
                "level": "info",
                "title": "Moving....",
                "message": "Moving downloaded file to storage folder",
            }
            RedisArchivist().set_message(self.MSG, mess_dict)

            if queue.has_item():
                message = "Continue with next video."
            else:
                message = "Download queue is finished."

            self.move_to_archive(vid_dict)
            mess_dict = {
                "status": self.MSG,
                "level": "info",
                "title": "Completed",
                "message": message,
            }
            RedisArchivist().set_message(self.MSG, mess_dict, expire=10)
            self._delete_from_pending(youtube_id)

        # post processing
        self._add_subscribed_channels()
        DownloadPostProcess(self).run()

    def _setup_queue(self):
        """setup required and validate"""
        if self.config["downloads"]["cookie_import"]:
            valid = CookieHandler(self.config).validate()
            if not valid:
                return

        pending = PendingList()
        pending.get_download()
        pending.get_channels()
        self.video_overwrites = pending.video_overwrites

    def add_pending(self):
        """add pending videos to download queue"""
        mess_dict = {
            "status": self.MSG,
            "level": "info",
            "title": "Looking for videos to download",
            "message": "Scanning your download queue.",
        }
        RedisArchivist().set_message(self.MSG, mess_dict, expire=True)
        pending = PendingList()
        pending.get_download()
        to_add = [
            json.dumps(
                {
                    "youtube_id": i["youtube_id"],
                    # Using .value in default val to match what would be
                    # decoded when parsing json if not set
                    "vid_type": i.get("vid_type", VideoTypeEnum.VIDEOS.value),
                }
            )
            for i in pending.all_pending
        ]
        if not to_add:
            # there is nothing pending
            print("download queue is empty")
            mess_dict = {
                "status": self.MSG,
                "level": "error",
                "title": "Download queue is empty",
                "message": "Add some videos to the queue first.",
            }
            RedisArchivist().set_message(self.MSG, mess_dict, expire=True)
            return

        RedisQueue(queue_name="dl_queue").add_list(to_add)

    def _progress_hook(self, response):
        """process the progress_hooks from yt_dlp"""
        title = "Downloading: " + response["info_dict"]["title"]

        try:
            percent = response["_percent_str"]
            size = response["_total_bytes_str"]
            speed = response["_speed_str"]
            eta = response["_eta_str"]
            message = f"{percent} of {size} at {speed} - time left: {eta}"
        except KeyError:
            message = "processing"

        mess_dict = {
            "status": self.MSG,
            "level": "info",
            "title": title,
            "message": message,
        }
        RedisArchivist().set_message(self.MSG, mess_dict, expire=True)

    def _build_obs(self):
        """collection to build all obs passed to yt-dlp"""
        self._build_obs_basic()
        self._build_obs_user()
        self._build_obs_postprocessors()

    def _build_obs_basic(self):
        """initial obs"""
        self.obs = {
            "default_search": "ytsearch",
            "merge_output_format": "mp4",
            "outtmpl": (
                self.config["application"]["cache_dir"]
                + "/download/%(id)s.mp4"
            ),
            "progress_hooks": [self._progress_hook],
            "noprogress": True,
            "quiet": True,
            "continuedl": True,
            "retries": 3,
            "writethumbnail": False,
            "noplaylist": True,
            "check_formats": "selected",
            "socket_timeout": 3,
        }

    def _build_obs_user(self):
        """build user customized options"""
        if self.config["downloads"]["format"]:
            self.obs["format"] = self.config["downloads"]["format"]
        if self.config["downloads"]["limit_speed"]:
            self.obs["ratelimit"] = (
                self.config["downloads"]["limit_speed"] * 1024
            )

        throttle = self.config["downloads"]["throttledratelimit"]
        if throttle:
            self.obs["throttledratelimit"] = throttle * 1024

    def _build_obs_postprocessors(self):
        """add postprocessor to obs"""
        postprocessors = []

        if self.config["downloads"]["add_metadata"]:
            postprocessors.append(
                {
                    "key": "FFmpegMetadata",
                    "add_chapters": True,
                    "add_metadata": True,
                }
            )
            postprocessors.append(
                {
                    "key": "MetadataFromField",
                    "formats": [
                        "%(title)s:%(meta_title)s",
                        "%(uploader)s:%(meta_artist)s",
                        ":(?P<album>)",
                    ],
                    "when": "pre_process",
                }
            )

        if self.config["downloads"]["add_thumbnail"]:
            postprocessors.append(
                {
                    "key": "EmbedThumbnail",
                    "already_have_thumbnail": True,
                }
            )
            self.obs["writethumbnail"] = True

        self.obs["postprocessors"] = postprocessors

    def get_format_overwrites(self, youtube_id):
        """get overwrites from single video"""
        overwrites = self.video_overwrites.get(youtube_id, False)
        if overwrites:
            return overwrites.get("download_format", False)

        return False

    def _dl_single_vid(self, youtube_id):
        """download single video"""
        obs = self.obs.copy()
        format_overwrite = self.get_format_overwrites(youtube_id)
        if format_overwrite:
            obs["format"] = format_overwrite

        dl_cache = self.config["application"]["cache_dir"] + "/download/"

        # check if already in cache to continue from there
        all_cached = ignore_filelist(os.listdir(dl_cache))
        for file_name in all_cached:
            if youtube_id in file_name:
                obs["outtmpl"] = os.path.join(dl_cache, file_name)

        success = YtWrap(obs, self.config).download(youtube_id)

        if self.obs["writethumbnail"]:
            # webp files don't get cleaned up automatically
            all_cached = ignore_filelist(os.listdir(dl_cache))
            to_clean = [i for i in all_cached if not i.endswith(".mp4")]
            for file_name in to_clean:
                file_path = os.path.join(dl_cache, file_name)
                os.remove(file_path)

        return success

    def move_to_archive(self, vid_dict):
        """move downloaded video from cache to archive"""
        videos = self.config["application"]["videos"]
        host_uid = self.config["application"]["HOST_UID"]
        host_gid = self.config["application"]["HOST_GID"]
        channel_name = clean_string(vid_dict["channel"]["channel_name"])
        if len(channel_name) <= 3:
            # fall back to channel id
            channel_name = vid_dict["channel"]["channel_id"]
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
        old_path = os.path.join(cache_dir, "download", old_file)
        new_path = os.path.join(videos, vid_dict["media_url"])
        # move media file and fix permission
        shutil.move(old_path, new_path, copy_function=shutil.copyfile)
        if host_uid and host_gid:
            os.chown(new_path, host_uid, host_gid)

    @staticmethod
    def _delete_from_pending(youtube_id):
        """delete downloaded video from pending index if its there"""
        path = f"ta_download/_doc/{youtube_id}"
        _, _ = ElasticWrap(path).delete()

    def _add_subscribed_channels(self):
        """add all channels subscribed to refresh"""
        all_subscribed = PlaylistSubscription().get_playlists()
        if not all_subscribed:
            return

        channel_ids = [i["playlist_channel_id"] for i in all_subscribed]
        for channel_id in channel_ids:
            self.channels.add(channel_id)

        return
