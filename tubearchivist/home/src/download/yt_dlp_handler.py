"""
functionality:
- handle yt_dlp
- build options and post processor
- download video files
- move to archive
"""

import os
import shutil
from datetime import datetime

from home.src.download.queue import PendingList
from home.src.download.subscriptions import PlaylistSubscription
from home.src.download.yt_dlp_base import YtWrap
from home.src.es.connect import ElasticWrap, IndexPaginate
from home.src.index.channel import YoutubeChannel
from home.src.index.comments import CommentList
from home.src.index.playlist import YoutubePlaylist
from home.src.index.video import YoutubeVideo, index_new_video
from home.src.index.video_constants import VideoTypeEnum
from home.src.ta.config import AppConfig
from home.src.ta.helper import clean_string, ignore_filelist


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
            channel = YoutubeChannel(channel_id, task=self.download.task)
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
        if not self.download.task:
            return

        total_channel = len(self.download.channels)
        total_playlist = len(all_channel_playlist)

        message = [
            f"Post Processing Channels: {id_c}/{total_channel}",
            f"Validate Playlists {id_p + 1}/{total_playlist}",
        ]
        progress = (id_c + 1) / total_channel
        self.download.task.send_progress(message, progress=progress)

    def get_comments(self):
        """get comments from youtube"""
        CommentList(self.download.videos, task=self.download.task).index()


class VideoDownloader:
    """
    handle the video download functionality
    if not initiated with list, take from queue
    """

    def __init__(self, youtube_id_list=False, task=False):
        self.obs = False
        self.video_overwrites = False
        self.youtube_id_list = youtube_id_list
        self.task = task
        self.config = AppConfig().config
        self._build_obs()
        self.channels = set()
        self.videos = set()

    def run_queue(self, auto_only=False):
        """setup download queue in redis loop until no more items"""
        self._get_overwrites()
        while True:
            video_data = self._get_next(auto_only)
            if self.task.is_stopped() or not video_data:
                break

            youtube_id = video_data.get("youtube_id")
            print(f"{youtube_id}: Downloading video")
            self._notify(video_data, "Validate download format")

            success = self._dl_single_vid(youtube_id)
            if not success:
                continue

            self._notify(video_data, "Add video metadata to index")

            vid_dict = index_new_video(
                youtube_id,
                video_overwrites=self.video_overwrites,
                video_type=VideoTypeEnum(video_data["vid_type"]),
            )
            self.channels.add(vid_dict["channel"]["channel_id"])
            self.videos.add(vid_dict["youtube_id"])

            self._notify(video_data, "Move downloaded file to archive")
            self.move_to_archive(vid_dict)
            self._delete_from_pending(youtube_id)

        # post processing
        self._add_subscribed_channels()
        DownloadPostProcess(self).run()

    def _notify(self, video_data, message):
        """send progress notification to task"""
        if not self.task:
            return

        typ = VideoTypeEnum(video_data["vid_type"]).value.rstrip("s").title()
        title = video_data.get("title")
        self.task.send_progress([f"Processing {typ}: {title}", message])

    def _get_next(self, auto_only):
        """get next item in queue"""
        must_list = [{"term": {"status": {"value": "pending"}}}]
        if auto_only:
            must_list.append({"term": {"auto_start": {"value": True}}})

        data = {
            "size": 1,
            "query": {"bool": {"must": must_list}},
            "sort": [
                {"auto_start": {"order": "desc"}},
                {"timestamp": {"order": "asc"}},
            ],
        }
        path = "ta_download/_search"
        response, _ = ElasticWrap(path).get(data=data)
        if not response["hits"]["hits"]:
            return False

        return response["hits"]["hits"][0]["_source"]

    def _get_overwrites(self):
        """get channel overwrites"""
        pending = PendingList()
        pending.get_download()
        pending.get_channels()
        self.video_overwrites = pending.video_overwrites

    def _progress_hook(self, response):
        """process the progress_hooks from yt_dlp"""
        progress = False
        try:
            size = response.get("_total_bytes_str")
            if size.strip() == "N/A":
                size = response.get("_total_bytes_estimate_str", "N/A")

            percent = response["_percent_str"]
            progress = float(percent.strip("%")) / 100
            speed = response["_speed_str"]
            eta = response["_eta_str"]
            message = f"{percent} of {size} at {speed} - time left: {eta}"
        except KeyError:
            message = "processing"

        if self.task:
            title = response["info_dict"]["title"]
            self.task.send_progress([title, message], progress=progress)

    def _build_obs(self):
        """collection to build all obs passed to yt-dlp"""
        self._build_obs_basic()
        self._build_obs_user()
        self._build_obs_postprocessors()

    def _build_obs_basic(self):
        """initial obs"""
        self.obs = {
            "merge_output_format": "mp4",
            "outtmpl": (
                self.config["application"]["cache_dir"]
                + "/download/%(id)s.mp4"
            ),
            "progress_hooks": [self._progress_hook],
            "noprogress": True,
            "continuedl": True,
            "writethumbnail": False,
            "noplaylist": True,
        }

    def _build_obs_user(self):
        """build user customized options"""
        if self.config["downloads"]["format"]:
            self.obs["format"] = self.config["downloads"]["format"]
        if self.config["downloads"]["format_sort"]:
            format_sort = self.config["downloads"]["format_sort"]
            format_sort_list = [i.strip() for i in format_sort.split(",")]
            self.obs["format_sort"] = format_sort_list
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
        path = f"ta_download/_doc/{youtube_id}?refresh=true"
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
