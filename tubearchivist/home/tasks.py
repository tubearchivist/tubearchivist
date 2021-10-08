"""
Functionality:
- initiate celery app
- collect tasks
"""

import os

from celery import Celery, shared_task
from home.src.config import AppConfig
from home.src.download import ChannelSubscription, PendingList, VideoDownloader
from home.src.helper import RedisArchivist, RedisQueue
from home.src.index_management import backup_all_indexes, restore_from_backup
from home.src.reindex import (
    ManualImport,
    reindex_old_documents,
    scan_filesystem,
)

CONFIG = AppConfig().config
REDIS_HOST = os.environ.get("REDIS_HOST")
REDIS_PORT = os.environ.get("REDIS_PORT")

if not REDIS_PORT:
    REDIS_PORT = 6379

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "home.settings")
app = Celery("tasks", broker=f"redis://{REDIS_HOST}:{REDIS_PORT}")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@shared_task
def update_subscribed():
    """look for missing videos and add to pending"""
    channel_handler = ChannelSubscription()
    missing_videos = channel_handler.find_missing()
    if missing_videos:
        pending_handler = PendingList()
        pending_handler.add_to_pending(missing_videos)
    # check if reindex is needed
    check_reindex.delay()


@shared_task
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
    queue = RedisQueue("dl_queue")
    queue.add_priority(youtube_id)
    print("Added to queue with priority: " + youtube_id)
    # start queue if needed
    have_lock = False
    my_lock = RedisArchivist().get_lock("downloading")

    try:
        have_lock = my_lock.acquire(blocking=False)
        if have_lock:
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
    pending_handler = PendingList()
    missing_videos = pending_handler.parse_url_list(youtube_ids)
    pending_handler.add_to_pending(missing_videos)


@shared_task
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
            import_handler = ManualImport()
            if import_handler.identified:
                import_handler.process_import()
        else:
            print("Did not acquire lock form import.")

    finally:
        if have_lock:
            my_lock.release()


@shared_task
def run_backup():
    """called from settings page, dump backup to zip file"""
    backup_all_indexes()
    print("backup finished")


@shared_task
def run_restore_backup():
    """called from settings page, dump backup to zip file"""
    restore_from_backup()
    print("index restore finished")


def kill_dl(task_id):
    """kill download worker task by ID"""
    app.control.revoke(task_id, terminate=True)
    _ = RedisArchivist().del_message("dl_queue_id")
    RedisQueue("dl_queue").clear()

    # clear cache
    cache_dir = os.path.join(CONFIG["application"]["cache_dir"], "download")
    for cached in os.listdir(cache_dir):
        to_delete = os.path.join(cache_dir, cached)
        os.remove(to_delete)

    # notify
    mess_dict = {
        "status": "downloading",
        "level": "error",
        "title": "Brutally killing download queue",
        "message": "",
    }
    RedisArchivist().set_message("progress:download", mess_dict)


@shared_task
def rescan_filesystem():
    """check the media folder for mismatches"""
    scan_filesystem()
