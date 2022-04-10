"""handle custom startup functions"""

import os
import sys

from django.apps import AppConfig
from home.src.es.connect import ElasticWrap
from home.src.es.index_setup import index_check
from home.src.ta.config import AppConfig as ArchivistConfig
from home.src.ta.ta_redis import RedisArchivist


class StartupCheck:
    """checks to run at application startup"""

    MIN_MAJOR, MAX_MAJOR = 7, 7
    MIN_MINOR = 17

    def __init__(self):
        self.config_handler = ArchivistConfig()
        self.redis_con = RedisArchivist()
        self.has_run = self.get_has_run()

    def run(self):
        """run all startup checks"""
        print("run startup checks")
        self.es_version_check()
        self.release_lock()
        index_check()
        self.sync_redis_state()
        self.make_folders()
        self.set_has_run()

    def get_has_run(self):
        """validate if check has already executed"""
        return self.redis_con.get_message("startup_check")

    def set_has_run(self):
        """startup checks run"""
        message = {"status": True}
        self.redis_con.set_message("startup_check", message, expire=120)

    def sync_redis_state(self):
        """make sure redis gets new config.json values"""
        print("sync redis")
        self.config_handler.load_new_defaults()

    def make_folders(self):
        """make needed cache folders here so docker doesn't mess it up"""
        folders = [
            "download",
            "channels",
            "videos",
            "playlists",
            "import",
            "backup",
        ]
        cache_dir = self.config_handler.config["application"]["cache_dir"]
        for folder in folders:
            folder_path = os.path.join(cache_dir, folder)
            try:
                os.makedirs(folder_path)
            except FileExistsError:
                continue

    def release_lock(self):
        """make sure there are no leftover locks set in redis"""
        all_locks = [
            "startup_check",
            "manual_import",
            "downloading",
            "dl_queue",
            "dl_queue_id",
            "rescan",
        ]
        for lock in all_locks:
            response = self.redis_con.del_message(lock)
            if response:
                print("deleted leftover key from redis: " + lock)

    def is_invalid(self, version):
        """return true if es version is invalid, false if ok"""
        major, minor = [int(i) for i in version.split(".")[:2]]
        if not self.MIN_MAJOR <= major <= self.MAX_MAJOR:
            return True

        if minor >= self.MIN_MINOR:
            return False

        return True

    def es_version_check(self):
        """check for minimal elasticsearch version"""
        response, _ = ElasticWrap("/").get()
        version = response["version"]["number"]
        invalid = self.is_invalid(version)

        if invalid:
            print(
                "required elasticsearch version: "
                + f"{self.MIN_MAJOR}.{self.MIN_MINOR}"
            )
            sys.exit(1)

        print("elasticsearch version check passed")


class HomeConfig(AppConfig):
    """call startup funcs"""

    default_auto_field = "django.db.models.BigAutoField"
    name = "home"

    def ready(self):
        startup = StartupCheck()
        if startup.has_run["status"]:
            print("startup checks run in other thread")
            return

        startup.run()
