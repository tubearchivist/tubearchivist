"""
Functionality:
- initiate celery app
- collect tasks
- user config changes won't get applied here
  because tasks are initiated at application start
"""

import os

from celery import Celery, Task, shared_task
from home.src.download.queue import PendingList
from home.src.download.subscriptions import (
    SubscriptionHandler,
    SubscriptionScanner,
)
from home.src.download.thumbnails import ThumbFilesystem, ThumbValidator
from home.src.download.yt_dlp_handler import VideoDownloader
from home.src.es.backup import ElasticBackup
from home.src.es.index_setup import ElasitIndexWrap
from home.src.index.channel import YoutubeChannel
from home.src.index.filesystem import Filesystem
from home.src.index.manual import ImportFolderScanner
from home.src.index.reindex import Reindex, ReindexManual, ReindexPopulate
from home.src.ta.config import AppConfig, ReleaseVersion, ScheduleBuilder
from home.src.ta.ta_redis import RedisArchivist
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


class BaseTask(Task):
    """base class to inherit each class from"""

    # pylint: disable=abstract-method

    TASK_CONFIG = {
        "update_subscribed": {
            "title": "Rescan your Subscriptions",
            "group": "download:scan",
            "api-start": True,
            "api-stop": True,
        },
        "download_pending": {
            "title": "Downloading",
            "group": "download:run",
            "api-start": True,
            "api-stop": True,
        },
        "extract_download": {
            "title": "Add to download queue",
            "group": "download:add",
            "api-stop": True,
        },
        "check_reindex": {
            "title": "Reindex Documents",
            "group": "reindex:run",
        },
        "manual_import": {
            "title": "Manual video import",
            "group": "setting:import",
            "api-start": True,
        },
        "run_backup": {
            "title": "Index Backup",
            "group": "setting:backup",
            "api-start": True,
        },
        "restore_backup": {
            "title": "Restore Backup",
            "group": "setting:restore",
        },
        "rescan_filesystem": {
            "title": "Rescan your Filesystem",
            "group": "setting:filesystemscan",
            "api-start": True,
        },
        "thumbnail_check": {
            "title": "Check your Thumbnails",
            "group": "setting:thumbnailcheck",
            "api-start": True,
        },
        "resync_thumbs": {
            "title": "Sync Thumbnails to Media Files",
            "group": "setting:thumbnailsync",
            "api-start": True,
        },
        "index_playlists": {
            "title": "Index Channel Playlist",
            "group": "channel:indexplaylist",
        },
        "subscribe_to": {
            "title": "Add Subscription",
            "group": "subscription:add",
        },
    }

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """callback for task failure"""
        print(f"{task_id} Failed callback")
        message, key = self._build_message(level="error")
        message.update({"messages": ["Task failed"]})
        RedisArchivist().set_message(key, message, expire=20)

    def on_success(self, retval, task_id, args, kwargs):
        """callback task completed successfully"""
        print(f"{task_id} success callback")
        message, key = self._build_message()
        message.update({"messages": ["Task completed successfully"]})
        RedisArchivist().set_message(key, message, expire=5)

    def before_start(self, task_id, args, kwargs):
        """callback before initiating task"""
        print(f"{self.name} create callback")
        message, key = self._build_message()
        message.update({"messages": ["New task received."]})
        RedisArchivist().set_message(key, message)

    def send_progress(self, message_lines, progress=False, title=False):
        """send progress message"""
        message, key = self._build_message()
        message.update(
            {
                "messages": message_lines,
                "progress": progress,
            }
        )
        if title:
            message["title"] = title

        RedisArchivist().set_message(key, message)

    def _build_message(self, level="info"):
        """build message dict"""
        task_id = self.request.id
        message = self.TASK_CONFIG.get(self.name).copy()
        message.update({"level": level, "id": task_id})
        task_result = TaskManager().get_task(task_id)
        if task_result:
            command = task_result.get("command", False)
            message.update({"command": command})

        key = f"message:{message.get('group')}:{task_id.split('-')[0]}"
        return message, key

    def is_stopped(self):
        """check if task is stopped"""
        return TaskManager().is_stopped(self.request.id)


@shared_task(name="update_subscribed", bind=True, base=BaseTask)
def update_subscribed(self):
    """look for missing videos and add to pending"""
    manager = TaskManager()
    if manager.is_pending(self):
        print(f"[task][{self.name}] rescan already running")
        self.send_progress("Rescan already in progress.")
        return

    manager.init(self)
    handler = SubscriptionScanner(task=self)
    missing_videos = handler.scan()
    auto_start = handler.auto_start
    if missing_videos:
        print(missing_videos)
        extrac_dl.delay(missing_videos, auto_start=auto_start)


@shared_task(name="download_pending", bind=True, base=BaseTask)
def download_pending(self, auto_only=False):
    """download latest pending videos"""
    manager = TaskManager()
    if manager.is_pending(self):
        print(f"[task][{self.name}] download queue already running")
        self.send_progress("Download Queue is already running.")
        return

    manager.init(self)
    VideoDownloader(task=self).run_queue(auto_only=auto_only)


@shared_task(name="extract_download", bind=True, base=BaseTask)
def extrac_dl(self, youtube_ids, auto_start=False):
    """parse list passed and add to pending"""
    TaskManager().init(self)
    if isinstance(youtube_ids, str):
        to_add = Parser(youtube_ids).parse()
    else:
        to_add = youtube_ids

    pending_handler = PendingList(youtube_ids=to_add, task=self)
    pending_handler.parse_url_list()
    pending_handler.add_to_pending(auto_start=auto_start)

    if auto_start:
        download_pending.delay(auto_only=True)


@shared_task(bind=True, name="check_reindex", base=BaseTask)
def check_reindex(self, data=False, extract_videos=False):
    """run the reindex main command"""
    if data:
        # started from frontend through API
        print(f"[task][{self.name}] reindex {data}")
        self.send_progress("Add items to the reindex Queue.")
        ReindexManual(extract_videos=extract_videos).extract_data(data)

    manager = TaskManager()
    if manager.is_pending(self):
        print(f"[task][{self.name}] reindex queue is already running")
        self.send_progress("Reindex Queue is already running.")
        return

    manager.init(self)
    if not data:
        # started from scheduler
        populate = ReindexPopulate()
        print(f"[task][{self.name}] reindex outdated documents")
        self.send_progress("Add recent documents to the reindex Queue.")
        populate.add_recent()
        self.send_progress("Add outdated documents to the reindex Queue.")
        populate.add_outdated()

    Reindex(task=self).reindex_all()


@shared_task(bind=True, name="manual_import", base=BaseTask)
def run_manual_import(self):
    """called from settings page, to go through import folder"""
    manager = TaskManager()
    if manager.is_pending(self):
        print(f"[task][{self.name}] manual import is already running")
        self.send_progress("Manual import is already running.")
        return

    manager.init(self)
    ImportFolderScanner(task=self).scan()


@shared_task(bind=True, name="run_backup", base=BaseTask)
def run_backup(self, reason="auto"):
    """called from settings page, dump backup to zip file"""
    manager = TaskManager()
    if manager.is_pending(self):
        print(f"[task][{self.name}] backup is already running")
        self.send_progress("Backup is already running.")
        return

    manager.init(self)
    ElasticBackup(reason=reason, task=self).backup_all_indexes()


@shared_task(bind=True, name="restore_backup", base=BaseTask)
def run_restore_backup(self, filename):
    """called from settings page, dump backup to zip file"""
    manager = TaskManager()
    if manager.is_pending(self):
        print(f"[task][{self.name}] restore is already running")
        self.send_progress("Restore is already running.")
        return

    manager.init(self)
    self.send_progress(["Reset your Index"])
    ElasitIndexWrap().reset()
    ElasticBackup(task=self).restore(filename)
    print("index restore finished")


@shared_task(bind=True, name="rescan_filesystem", base=BaseTask)
def rescan_filesystem(self):
    """check the media folder for mismatches"""
    manager = TaskManager()
    if manager.is_pending(self):
        print(f"[task][{self.name}] filesystem rescan already running")
        self.send_progress("Filesystem Rescan is already running.")
        return

    manager.init(self)
    Filesystem(task=self).process()
    ThumbValidator(task=self).validate()


@shared_task(bind=True, name="thumbnail_check", base=BaseTask)
def thumbnail_check(self):
    """validate thumbnails"""
    manager = TaskManager()
    if manager.is_pending(self):
        print(f"[task][{self.name}] thumbnail check is already running")
        self.send_progress("Thumbnail check is already running.")
        return

    manager.init(self)
    ThumbValidator(task=self).validate()


@shared_task(bind=True, name="resync_thumbs", base=BaseTask)
def re_sync_thumbs(self):
    """sync thumbnails to mediafiles"""
    manager = TaskManager()
    if manager.is_pending(self):
        print(f"[task][{self.name}] thumb re-embed is already running")
        self.send_progress("Thumbnail re-embed is already running.")
        return

    manager.init(self)
    ThumbFilesystem(task=self).embed()


@shared_task(bind=True, name="subscribe_to", base=BaseTask)
def subscribe_to(self, url_str):
    """take a list of urls to subscribe to"""
    SubscriptionHandler(url_str, task=self).subscribe()


@shared_task(bind=True, name="index_playlists", base=BaseTask)
def index_channel_playlists(self, channel_id):
    """add all playlists of channel to index"""
    channel = YoutubeChannel(channel_id, task=self)
    channel.index_channel_playlists()


@shared_task(name="version_check")
def version_check():
    """check for new updates"""
    ReleaseVersion().check()


# start schedule here
app.conf.beat_schedule = ScheduleBuilder().build_schedule()
