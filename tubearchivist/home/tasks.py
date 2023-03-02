"""
Functionality:
- initiate celery app
- collect tasks
- user config changes won't get applied here
  because tasks are initiated at application start
"""

import json
import os

from celery import Celery, shared_task
from home.src.download.queue import PendingList
from home.src.download.subscriptions import (
    ChannelSubscription,
    PlaylistSubscription,
    SubscriptionScanner,
)
from home.src.download.thumbnails import ThumbFilesystem, ThumbValidator
from home.src.download.yt_dlp_handler import VideoDownloader
from home.src.es.backup import ElasticBackup
from home.src.es.index_setup import ElasitIndexWrap
from home.src.index.channel import YoutubeChannel
from home.src.index.filesystem import ImportFolderScanner, scan_filesystem
from home.src.index.reindex import Reindex, ReindexManual, ReindexOutdated
from home.src.index.video_constants import VideoTypeEnum
from home.src.ta.config import AppConfig, ReleaseVersion, ScheduleBuilder
from home.src.ta.helper import clear_dl_cache
from home.src.ta.ta_redis import RedisArchivist, RedisQueue
from home.src.ta.task_manager import TaskManager
from home.src.ta.urlparser import Parser

CONFIG = AppConfig().config
REDIS_HOST = os.environ.get("REDIS_HOST")
REDIS_PORT = os.environ.get("REDIS_PORT") or 6379

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
app = Celery(
    "tasks",
    broker=f"redis://{REDIS_HOST}:{REDIS_PORT}",
    backend=f"redis://{REDIS_HOST}:{REDIS_PORT}",
    result_extended=True,
)
app.config_from_object("django.conf:settings", namespace="ta:")
app.autodiscover_tasks()
app.conf.timezone = os.environ.get("TZ") or "UTC"


@shared_task(name="update_subscribed", bind=True)
def update_subscribed(self):
    """look for missing videos and add to pending"""
    manager = TaskManager()
    if manager.is_pending(self):
        print(f"[task][{self.name}] rescan already running")
        message = {
            "status": "message:rescan",
            "level": "error",
            "title": "Rescanning channels and playlists.",
            "message": "Rescan already in progress.",
        }
        RedisArchivist().set_message("message:rescan", message, expire=True)
        return

    manager.init(self)
    SubscriptionScanner().scan()


@shared_task(name="download_pending", bind=True)
def download_pending(self):
    """download latest pending videos"""
    manager = TaskManager()
    if manager.is_pending(self):
        print(f"[task][{self.name}] download queue already running")
        return

    manager.init(self)
    downloader = VideoDownloader()
    downloader.add_pending()
    downloader.run_queue()


@shared_task(name="download_single")
def download_single(pending_video):
    """start download single video now"""
    queue = RedisQueue(queue_name="dl_queue")

    to_add = {
        "youtube_id": pending_video["youtube_id"],
        "vid_type": pending_video.get("vid_type", VideoTypeEnum.VIDEOS.value),
    }
    queue.add_priority(json.dumps(to_add))
    print(f"Added to queue with priority: {to_add}")
    # start queue if needed
    have_lock = False
    my_lock = RedisArchivist().get_lock("downloading")

    try:
        have_lock = my_lock.acquire(blocking=False)
        if have_lock:
            key = "message:download"
            mess_dict = {
                "status": key,
                "level": "info",
                "title": "Download single video",
                "message": "processing",
            }
            RedisArchivist().set_message(key, mess_dict, expire=True)
            VideoDownloader().run_queue()
        else:
            print("Download queue already running.")

    finally:
        # release if only single run
        if have_lock and not queue.get_next():
            my_lock.release()


@shared_task(name="extract_download")
def extrac_dl(youtube_ids):
    """parse list passed and add to pending"""
    pending_handler = PendingList(youtube_ids=youtube_ids)
    pending_handler.parse_url_list()
    pending_handler.add_to_pending()


@shared_task(bind=True, name="check_reindex")
def check_reindex(self, data=False, extract_videos=False):
    """run the reindex main command"""
    if data:
        # started from frontend through API
        print(f"[task][{self.name}] reindex {data}")
        ReindexManual(extract_videos=extract_videos).extract_data(data)

    manager = TaskManager()
    if manager.is_pending(self):
        print(f"[task][{self.name}] reindex queue is already running")
        return

    manager.init(self)
    if not data:
        # started from scheduler
        print(f"[task][{self.name}] reindex outdated documents")
        ReindexOutdated().add_outdated()

    Reindex().reindex_all()


@shared_task(bind=True, name="manual_import")
def run_manual_import(self):
    """called from settings page, to go through import folder"""
    manager = TaskManager()
    if manager.is_pending(self):
        print(f"[task][{self.name}] manual import is already running")
        return

    manager.init(self)
    ImportFolderScanner().scan()


@shared_task(bind=True, name="run_backup")
def run_backup(self, reason="auto"):
    """called from settings page, dump backup to zip file"""
    manager = TaskManager()
    if manager.is_pending(self):
        print(f"[task][{self.name}] backup is already running")
        return

    manager.init(self)
    ElasticBackup(reason=reason).backup_all_indexes()


@shared_task(name="restore_backup")
def run_restore_backup(filename):
    """called from settings page, dump backup to zip file"""
    ElasitIndexWrap().reset()
    ElasticBackup().restore(filename)
    print("index restore finished")


@shared_task(name="kill_download")
def kill_dl(task_id):
    """kill download worker task by ID"""
    if task_id:
        app.control.revoke(task_id, terminate=True)

    _ = RedisArchivist().del_message("dl_queue_id")
    RedisQueue(queue_name="dl_queue").clear()

    _ = clear_dl_cache(CONFIG)

    # notify
    mess_dict = {
        "status": "message:download",
        "level": "error",
        "title": "Canceling download process",
        "message": "Canceling download queue now.",
    }
    RedisArchivist().set_message("message:download", mess_dict, expire=True)


@shared_task(name="rescan_filesystem")
def rescan_filesystem():
    """check the media folder for mismatches"""
    scan_filesystem()
    ThumbValidator().download_missing()


@shared_task(name="thumbnail_check")
def thumbnail_check():
    """validate thumbnails"""
    ThumbValidator().download_missing()


@shared_task(name="resync_thumbs")
def re_sync_thumbs():
    """sync thumbnails to mediafiles"""
    ThumbFilesystem().sync()


@shared_task(name="subscribe_to")
def subscribe_to(url_str):
    """take a list of urls to subscribe to"""
    to_subscribe_list = Parser(url_str).parse()
    for idx, item in enumerate(to_subscribe_list):
        to_sub_id = item["url"]
        if item["type"] == "playlist":
            PlaylistSubscription().process_url_str([item])
            continue

        if item["type"] == "video":
            vid_details = PendingList().get_youtube_details(to_sub_id)
            channel_id_sub = vid_details["channel_id"]
        elif item["type"] == "channel":
            channel_id_sub = to_sub_id
        else:
            raise ValueError("failed to subscribe to: " + to_sub_id)

        ChannelSubscription().change_subscribe(
            channel_id_sub, channel_subscribed=True
        )
        # notify for channels
        key = "message:subchannel"
        message = {
            "status": key,
            "level": "info",
            "title": "Subscribing to Channels",
            "message": f"Processing {idx + 1} of {len(to_subscribe_list)}",
        }
        RedisArchivist().set_message(key, message=message, expire=True)


@shared_task(name="index_playlists")
def index_channel_playlists(channel_id):
    """add all playlists of channel to index"""
    channel = YoutubeChannel(channel_id)
    # notify
    key = "message:playlistscan"
    mess_dict = {
        "status": key,
        "level": "info",
        "title": "Looking for playlists",
        "message": f"{channel_id}: Channel scan in progress",
    }
    RedisArchivist().set_message(key, mess_dict, expire=True)
    channel.index_channel_playlists()


@shared_task(name="version_check")
def version_check():
    """check for new updates"""
    ReleaseVersion().check()


# start schedule here
app.conf.beat_schedule = ScheduleBuilder().build_schedule()
