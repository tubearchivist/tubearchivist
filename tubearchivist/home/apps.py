"""handle custom startup functions"""

import os

from django.apps import AppConfig
from home.src.config import AppConfig as ArchivistConfig
from home.src.helper import RedisArchivist
from home.src.index_management import index_check


def sync_redis_state():
    """make sure redis gets new config.json values"""
    print("sync redis")
    config_handler = ArchivistConfig()
    config_handler.load_new_defaults()


def make_folders():
    """make needed cache folders here so docker doesn't mess it up"""
    folders = [
        "download",
        "channels",
        "videos",
        "playlists",
        "import",
        "backup",
    ]
    config = ArchivistConfig().config
    cache_dir = config["application"]["cache_dir"]
    for folder in folders:
        folder_path = os.path.join(cache_dir, folder)
        try:
            os.makedirs(folder_path)
        except FileExistsError:
            continue


def release_lock():
    """make sure there are no leftover locks set in redis on container start"""
    all_locks = [
        "manual_import",
        "downloading",
        "dl_queue",
        "dl_queue_id",
        "rescan",
    ]
    for lock in all_locks:
        response = RedisArchivist().del_message(lock)
        if response:
            print("deleted leftover key from redis: " + lock)


class HomeConfig(AppConfig):
    """call startup funcs"""

    default_auto_field = "django.db.models.BigAutoField"
    name = "home"

    def ready(self):
        release_lock()
        index_check()
        sync_redis_state()
        make_folders()
