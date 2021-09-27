""" handle startup """

import os

from home.src.config import AppConfig
from home.src.helper import del_message, set_message
from home.src.index_management import index_check

from .tasks import app as celery_app


def sync_redis_state():
    """make sure redis gets the config.json values"""
    print("sync redis")
    config_handler = AppConfig()
    config_handler.load_new_defaults()
    config = config_handler.config
    sort_order = config["archive"]["sort"]
    set_message("sort_order", sort_order, expire=False)
    hide_watched = bool(int(config["archive"]["hide_watched"]))
    set_message("hide_watched", hide_watched, expire=False)
    show_subed_only = bool(int(config["archive"]["show_subed_only"]))
    set_message("show_subed_only", show_subed_only, expire=False)


def make_folders():
    """make needed cache folders here so docker doesn't mess it up"""
    folders = ["download", "channels", "videos", "import", "backup"]
    config = AppConfig().config
    cache_dir = config["application"]["cache_dir"]
    for folder in folders:
        folder_path = os.path.join(cache_dir, folder)
        try:
            os.makedirs(folder_path)
        except FileExistsError:
            continue


def release_lock():
    """make sure there are no leftover locks set in redis on container start"""
    all_locks = ["manual_import", "downloading"]
    for lock in all_locks:
        print("release leftover lock: " + lock)
        del_message(lock)


__all__ = ("celery_app",)
make_folders()
sync_redis_state()
index_check()
release_lock()
