"""
Functionality:
- Static Task config values
- Type definitions
- separate to avoid circular imports
"""

from typing import TypedDict


class TaskItemConfig(TypedDict):
    """describes a task item config"""

    title: str
    group: str
    api_start: bool
    api_stop: bool


UPDATE_SUBSCRIBED: TaskItemConfig = {
    "title": "Rescan your Subscriptions",
    "group": "download:scan",
    "api_start": True,
    "api_stop": True,
}

DOWNLOAD_PENDING: TaskItemConfig = {
    "title": "Downloading",
    "group": "download:run",
    "api_start": True,
    "api_stop": True,
}

EXTRACT_DOWNLOAD: TaskItemConfig = {
    "title": "Add to download queue",
    "group": "download:add",
    "api_start": False,
    "api_stop": True,
}

CHECK_REINDEX: TaskItemConfig = {
    "title": "Reindex Documents",
    "group": "reindex:run",
    "api_start": False,
    "api_stop": False,
}

MANUAL_IMPORT: TaskItemConfig = {
    "title": "Manual video import",
    "group": "setting:import",
    "api_start": True,
    "api_stop": False,
}

RUN_BACKUP: TaskItemConfig = {
    "title": "Index Backup",
    "group": "setting:backup",
    "api_start": True,
    "api_stop": False,
}

RESTORE_BACKUP: TaskItemConfig = {
    "title": "Restore Backup",
    "group": "setting:restore",
    "api_start": False,
    "api_stop": False,
}

RESCAN_FILESYSTEM: TaskItemConfig = {
    "title": "Rescan your Filesystem",
    "group": "setting:filesystemscan",
    "api_start": True,
    "api_stop": False,
}

THUMBNAIL_CHECK: TaskItemConfig = {
    "title": "Check your Thumbnails",
    "group": "setting:thumbnailcheck",
    "api_start": True,
    "api_stop": False,
}

RESYNC_THUMBS: TaskItemConfig = {
    "title": "Sync Thumbnails to Media Files",
    "group": "setting:thumbnailsync",
    "api_start": True,
    "api_stop": False,
}

INDEX_PLAYLISTS: TaskItemConfig = {
    "title": "Index Channel Playlist",
    "group": "channel:indexplaylist",
    "api_start": False,
    "api_stop": False,
}

SUBSCRIBE_TO: TaskItemConfig = {
    "title": "Add Subscription",
    "group": "subscription:add",
    "api_start": False,
    "api_stop": False,
}

VERSION_CHECK: TaskItemConfig = {
    "title": "Look for new Version",
    "group": "",
    "api_start": False,
    "api_stop": False,
}

TASK_CONFIG: dict[str, TaskItemConfig] = {
    "update_subscribed": UPDATE_SUBSCRIBED,
    "download_pending": DOWNLOAD_PENDING,
    "extract_download": EXTRACT_DOWNLOAD,
    "check_reindex": CHECK_REINDEX,
    "manual_import": MANUAL_IMPORT,
    "run_backup": RUN_BACKUP,
    "restore_backup": RESTORE_BACKUP,
    "rescan_filesystem": RESCAN_FILESYSTEM,
    "thumbnail_check": THUMBNAIL_CHECK,
    "resync_thumbs": RESYNC_THUMBS,
    "index_playlists": INDEX_PLAYLISTS,
    "subscribe_to": SUBSCRIBE_TO,
    "version_check": VERSION_CHECK,
}
