"""
Functionality:
- initiate celery app
- collect tasks
- user config changes won't get applied here
  because tasks are initiated at application start
"""

import os

from celery import Celery, shared_task
from home.apps import StartupCheck
from home.src.download.queue import PendingList
from home.src.download.subscriptions import (
    ChannelSubscription,
    PlaylistSubscription,
)
from home.src.download.thumbnails import ThumbFilesystem, ThumbValidator
from home.src.download.yt_dlp_handler import VideoDownloader
from home.src.es.backup import ElasticBackup
from home.src.es.index_setup import ElasitIndexWrap
from home.src.index.channel import YoutubeChannel
from home.src.index.filesystem import (
    ImportFolderScanner,
    reindex_old_documents,
    scan_filesystem,
)
from home.src.ta.config import AppConfig, ScheduleBuilder
from home.src.ta.helper import UrlListParser, clear_dl_cache
from home.src.ta.ta_redis import RedisArchivist, RedisQueue

CONFIG = AppConfig().config
REDIS_HOST = os.environ.get("REDIS_HOST")
REDIS_PORT = os.environ.get("REDIS_PORT") or 6379

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
app = Celery("tasks", broker=f"redis://{REDIS_HOST}:{REDIS_PORT}")
app.config_from_object("django.conf:settings", namespace="ta:")
app.autodiscover_tasks()
app.conf.timezone = os.environ.get("TZ") or "UTC"


@shared_task(name="update_subscribed")
def update_subscribed():
    """look for missing videos and add to pending"""
    message = {
        "status": "message:rescan",
        "level": "info",
        "title": "Rescanning channels and playlists.",
        "message": "Looking for new videos.",
    }
    RedisArchivist().set_message("message:rescan", message, expire=True)

    have_lock = False
    my_lock = RedisArchivist().get_lock("rescan")

    try:
        have_lock = my_lock.acquire(blocking=False)
        if have_lock:
            channel_handler = ChannelSubscription()
            missing_from_channels = channel_handler.find_missing()
            playlist_handler = PlaylistSubscription()
            missing_from_playlists = playlist_handler.find_missing()
            missing = missing_from_channels + missing_from_playlists
            if missing:
                youtube_ids = [{"type": "video", "url": i} for i in missing]
                pending_handler = PendingList(youtube_ids=youtube_ids)
                pending_handler.parse_url_list()
                pending_handler.add_to_pending()

        else:
            print("Did not acquire rescan lock.")

    finally:
        if have_lock:
            my_lock.release()


@shared_task(name="download_pending")
def download_pending():
    """download latest pending videos"""
    have_lock = False
    my_lock = RedisArchivist().get_lock("downloading")

    try:
        have_lock = my_lock.acquire(blocking=False)
        if have_lock:
            downloader = VideoDownloader()
            downloader.add_pending()
            downloader.run_queue()
        else:
            print("Did not acquire download lock.")

    finally:
        if have_lock:
            my_lock.release()


@shared_task
def download_single(youtube_id):
    """start download single video now"""
    queue = RedisQueue()
    queue.add_priority(youtube_id)
    print("Added to queue with priority: " + youtube_id)
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


@shared_task
def extrac_dl(youtube_ids):
    """parse list passed and add to pending"""
    pending_handler = PendingList(youtube_ids=youtube_ids)
    pending_handler.parse_url_list()
    pending_handler.add_to_pending()


@shared_task(name="check_reindex")
def check_reindex():
    """run the reindex main command"""
    reindex_old_documents()


@shared_task
def run_manual_import():
    """called from settings page, to go through import folder"""
    print("starting media file import")
    have_lock = False
    my_lock = RedisArchivist().get_lock("manual_import")

    try:
        have_lock = my_lock.acquire(blocking=False)
        if have_lock:
            ImportFolderScanner().scan()
        else:
            print("Did not acquire lock form import.")

    finally:
        if have_lock:
            my_lock.release()


@shared_task(name="run_backup")
def run_backup(reason="auto"):
    """called from settings page, dump backup to zip file"""
    have_lock = False
    my_lock = RedisArchivist().get_lock("run_backup")

    try:
        have_lock = my_lock.acquire(blocking=False)
        if have_lock:
            ElasticBackup(reason=reason).backup_all_indexes()
        else:
            print("Did not acquire lock for backup task.")
    finally:
        if have_lock:
            my_lock.release()
            print("backup finished")


@shared_task
def run_restore_backup(filename):
    """called from settings page, dump backup to zip file"""
    ElasitIndexWrap().reset()
    ElasticBackup().restore(filename)
    print("index restore finished")


def kill_dl(task_id):
    """kill download worker task by ID"""
    if task_id:
        app.control.revoke(task_id, terminate=True)

    _ = RedisArchivist().del_message("dl_queue_id")
    RedisQueue().clear()

    clear_dl_cache(CONFIG)

    # notify
    mess_dict = {
        "status": "message:download",
        "level": "error",
        "title": "Canceling download process",
        "message": "Canceling download queue now.",
    }
    RedisArchivist().set_message("message:download", mess_dict, expire=True)


@shared_task
def rescan_filesystem():
    """check the media folder for mismatches"""
    scan_filesystem()
    ThumbValidator().download_missing()


@shared_task(name="thumbnail_check")
def thumbnail_check():
    """validate thumbnails"""
    ThumbValidator().download_missing()


@shared_task
def re_sync_thumbs():
    """sync thumbnails to mediafiles"""
    ThumbFilesystem().sync()


@shared_task
def subscribe_to(url_str):
    """take a list of urls to subscribe to"""
    to_subscribe_list = UrlListParser(url_str).process_list()
    counter = 1
    for item in to_subscribe_list:
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
            "message": f"Processing {counter} of {len(to_subscribe_list)}",
        }
        RedisArchivist().set_message(key, message=message, expire=True)
        counter = counter + 1


@shared_task
def index_channel_playlists(channel_id):
    """add all playlists of channel to index"""
    channel = YoutubeChannel(channel_id)
    # notify
    key = "message:playlistscan"
    mess_dict = {
        "status": key,
        "level": "info",
        "title": "Looking for playlists",
        "message": f'Scanning channel "{channel.youtube_id}" in progress',
    }
    RedisArchivist().set_message(key, mess_dict, expire=True)
    channel.index_channel_playlists()


try:
    app.conf.beat_schedule = ScheduleBuilder().build_schedule()
except KeyError:
    # update path from v0.0.8 to v0.0.9 to load new defaults
    StartupCheck().sync_redis_state()
    app.conf.beat_schedule = ScheduleBuilder().build_schedule()
