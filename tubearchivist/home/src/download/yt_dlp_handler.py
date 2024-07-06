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
from home.src.ta.helper import get_channel_overwrites, ignore_filelist
from home.src.ta.settings import EnvironmentSettings
from home.src.ta.ta_redis import RedisQueue


class DownloaderBase:
    """base class for shared config"""

    CACHE_DIR = EnvironmentSettings.CACHE_DIR
    MEDIA_DIR = EnvironmentSettings.MEDIA_DIR
    CHANNEL_QUEUE = "download:channel"
    PLAYLIST_QUEUE = "download:playlist:full"
    PLAYLIST_QUICK = "download:playlist:quick"
    VIDEO_QUEUE = "download:video"

    def __init__(self, task):
        self.task = task
        self.config = AppConfig().config
        self.channel_overwrites = get_channel_overwrites()
        self.now = int(datetime.now().timestamp())


class VideoDownloader(DownloaderBase):
    """handle the video download functionality"""

    def __init__(self, task=False):
        super().__init__(task)
        self.obs = False
        self._build_obs()

    def run_queue(self, auto_only=False) -> tuple[int, int]:
        """setup download queue in redis loop until no more items"""
        downloaded = 0
        failed = 0
        while True:
            video_data = self._get_next(auto_only)
            if self.task.is_stopped() or not video_data:
                self._reset_auto()
                break

            youtube_id = video_data["youtube_id"]
            channel_id = video_data["channel_id"]
            print(f"{youtube_id}: Downloading video")
            self._notify(video_data, "Validate download format")

            success = self._dl_single_vid(youtube_id, channel_id)
            if not success:
                failed += 1
                continue

            self._notify(video_data, "Add video metadata to index", progress=1)
            video_type = VideoTypeEnum(video_data["vid_type"])
            vid_dict = index_new_video(youtube_id, video_type=video_type)
            RedisQueue(self.CHANNEL_QUEUE).add(channel_id)
            RedisQueue(self.VIDEO_QUEUE).add(youtube_id)

            self._notify(video_data, "Move downloaded file to archive")
            self.move_to_archive(vid_dict)
            self._delete_from_pending(youtube_id)
            downloaded += 1

        # post processing
        DownloadPostProcess(self.task).run()

        return downloaded, failed

    def _notify(self, video_data, message, progress=False):
        """send progress notification to task"""
        if not self.task:
            return

        typ = VideoTypeEnum(video_data["vid_type"]).value.rstrip("s").title()
        title = video_data.get("title")
        self.task.send_progress(
            [f"Processing {typ}: {title}", message], progress=progress
        )

    def _get_next(self, auto_only):
        """get next item in queue"""
        must_list = [{"term": {"status": {"value": "pending"}}}]
        must_not_list = [{"exists": {"field": "message"}}]
        if auto_only:
            must_list.append({"term": {"auto_start": {"value": True}}})

        data = {
            "size": 1,
            "query": {"bool": {"must": must_list, "must_not": must_not_list}},
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
            "outtmpl": (self.CACHE_DIR + "/download/%(id)s.mp4"),
            "progress_hooks": [self._progress_hook],
            "noprogress": True,
            "continuedl": True,
            "writethumbnail": False,
            "noplaylist": True,
            "color": "no_color",
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

    def _set_overwrites(self, obs: dict, channel_id: str) -> None:
        """add overwrites to obs"""
        overwrites = self.channel_overwrites.get(channel_id)
        if overwrites and overwrites.get("download_format"):
            obs["format"] = overwrites.get("download_format")

    def _dl_single_vid(self, youtube_id: str, channel_id: str) -> bool:
        """download single video"""
        obs = self.obs.copy()
        self._set_overwrites(obs, channel_id)
        dl_cache = os.path.join(self.CACHE_DIR, "download")

        success, message = YtWrap(obs, self.config).download(youtube_id)
        if not success:
            self._handle_error(youtube_id, message)

        if self.obs["writethumbnail"]:
            # webp files don't get cleaned up automatically
            all_cached = ignore_filelist(os.listdir(dl_cache))
            to_clean = [i for i in all_cached if not i.endswith(".mp4")]
            for file_name in to_clean:
                file_path = os.path.join(dl_cache, file_name)
                os.remove(file_path)

        return success

    @staticmethod
    def _handle_error(youtube_id, message):
        """store error message"""
        data = {"doc": {"message": message}}
        _, _ = ElasticWrap(f"ta_download/_update/{youtube_id}").post(data=data)

    def move_to_archive(self, vid_dict):
        """move downloaded video from cache to archive"""
        host_uid = EnvironmentSettings.HOST_UID
        host_gid = EnvironmentSettings.HOST_GID
        # make folder
        folder = os.path.join(
            self.MEDIA_DIR, vid_dict["channel"]["channel_id"]
        )
        if not os.path.exists(folder):
            os.makedirs(folder)
            if host_uid and host_gid:
                os.chown(folder, host_uid, host_gid)
        # move media file
        media_file = vid_dict["youtube_id"] + ".mp4"
        old_path = os.path.join(self.CACHE_DIR, "download", media_file)
        new_path = os.path.join(self.MEDIA_DIR, vid_dict["media_url"])
        # move media file and fix permission
        shutil.move(old_path, new_path, copy_function=shutil.copyfile)
        if host_uid and host_gid:
            os.chown(new_path, host_uid, host_gid)

    @staticmethod
    def _delete_from_pending(youtube_id):
        """delete downloaded video from pending index if its there"""
        path = f"ta_download/_doc/{youtube_id}?refresh=true"
        _, _ = ElasticWrap(path).delete()

    def _reset_auto(self):
        """reset autostart to defaults after queue stop"""
        path = "ta_download/_update_by_query"
        data = {
            "query": {"term": {"auto_start": {"value": True}}},
            "script": {
                "source": "ctx._source.auto_start = false",
                "lang": "painless",
            },
        }
        response, _ = ElasticWrap(path).post(data=data)
        updated = response.get("updated")
        if updated:
            print(f"[download] reset auto start on {updated} videos.")


class DownloadPostProcess(DownloaderBase):
    """handle task to run after download queue finishes"""

    def run(self):
        """run all functions"""
        self.auto_delete_all()
        self.auto_delete_overwrites()
        self.refresh_playlist()
        self.match_videos()
        self.get_comments()

    def auto_delete_all(self):
        """handle auto delete"""
        autodelete_days = self.config["downloads"]["autodelete_days"]
        if not autodelete_days:
            return

        print(f"auto delete older than {autodelete_days} days")
        now_lte = str(self.now - autodelete_days * 24 * 60 * 60)
        data = {
            "query": {"range": {"player.watched_date": {"lte": now_lte}}},
            "sort": [{"player.watched_date": {"order": "asc"}}],
        }
        self._auto_delete_watched(data)

    def auto_delete_overwrites(self):
        """handle per channel auto delete from overwrites"""
        for channel_id, value in self.channel_overwrites.items():
            if "autodelete_days" in value:
                autodelete_days = value.get("autodelete_days")
                print(f"{channel_id}: delete older than {autodelete_days}d")
                now_lte = str(self.now - autodelete_days * 24 * 60 * 60)
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
        _ = pending.add_to_pending(status="ignore")

    def refresh_playlist(self) -> None:
        """match videos with playlists"""
        self.add_playlists_to_refresh()

        queue = RedisQueue(self.PLAYLIST_QUEUE)
        while True:
            total = queue.max_score()
            playlist_id, idx = queue.get_next()
            if not playlist_id or not idx or not total:
                break

            playlist = YoutubePlaylist(playlist_id)
            playlist.update_playlist(skip_on_empty=True)

            if not self.task:
                continue

            channel_name = playlist.json_data["playlist_channel"]
            playlist_title = playlist.json_data["playlist_name"]
            message = [
                f"Post Processing Playlists for: {channel_name}",
                f"{playlist_title} [{idx}/{total}]",
            ]
            progress = idx / total
            self.task.send_progress(message, progress=progress)

    def add_playlists_to_refresh(self) -> None:
        """add playlists to refresh"""
        if self.task:
            message = ["Post Processing Playlists", "Scanning for Playlists"]
            self.task.send_progress(message)

        self._add_playlist_sub()
        self._add_channel_playlists()
        self._add_video_playlists()

    def _add_playlist_sub(self):
        """add subscribed playlists to refresh"""
        subs = PlaylistSubscription().get_playlists()
        to_add = [i["playlist_id"] for i in subs]
        RedisQueue(self.PLAYLIST_QUEUE).add_list(to_add)

    def _add_channel_playlists(self):
        """add playlists from channels to refresh"""
        queue = RedisQueue(self.CHANNEL_QUEUE)
        while True:
            channel_id, _ = queue.get_next()
            if not channel_id:
                break

            channel = YoutubeChannel(channel_id)
            channel.get_from_es()
            overwrites = channel.get_overwrites()
            if "index_playlists" in overwrites:
                channel.get_all_playlists()
                to_add = [i[0] for i in channel.all_playlists]
                RedisQueue(self.PLAYLIST_QUEUE).add_list(to_add)

    def _add_video_playlists(self):
        """add other playlists for quick sync"""
        all_playlists = RedisQueue(self.PLAYLIST_QUEUE).get_all()
        must_not = [{"terms": {"playlist_id": all_playlists}}]
        video_ids = RedisQueue(self.VIDEO_QUEUE).get_all()
        must = [{"terms": {"playlist_entries.youtube_id": video_ids}}]
        data = {
            "query": {"bool": {"must_not": must_not, "must": must}},
            "_source": ["playlist_id"],
        }
        playlists = IndexPaginate("ta_playlist", data).get_results()
        to_add = [i["playlist_id"] for i in playlists]
        RedisQueue(self.PLAYLIST_QUICK).add_list(to_add)

    def match_videos(self) -> None:
        """scan rest of indexed playlists to match videos"""
        queue = RedisQueue(self.PLAYLIST_QUICK)
        while True:
            total = queue.max_score()
            playlist_id, idx = queue.get_next()
            if not playlist_id or not idx or not total:
                break

            playlist = YoutubePlaylist(playlist_id)
            playlist.get_from_es()
            playlist.add_vids_to_playlist()
            playlist.remove_vids_from_playlist()

            if not self.task:
                continue

            message = [
                "Post Processing Playlists.",
                f"Validate Playlists: - {idx}/{total}",
            ]
            progress = idx / total
            self.task.send_progress(message, progress=progress)

    def get_comments(self):
        """get comments from youtube"""
        video_queue = RedisQueue(self.VIDEO_QUEUE)
        comment_list = CommentList(task=self.task)
        comment_list.add(video_ids=video_queue.get_all())

        video_queue.clear()
        comment_list.index()
