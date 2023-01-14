"""handle custom startup functions"""

import os
import sys

from django.apps import AppConfig
from home.src.es.connect import ElasticWrap
from home.src.es.index_setup import ElasitIndexWrap
from home.src.es.snapshot import ElasticSnapshot
from home.src.ta.config import AppConfig as ArchivistConfig
from home.src.ta.config import ReleaseVersion
from home.src.ta.helper import clear_dl_cache
from home.src.ta.ta_redis import RedisArchivist


class StartupCheck:
    """checks to run at application startup"""

    MIN_MAJOR, MAX_MAJOR = 8, 8
    MIN_MINOR = 0

    def __init__(self):
        self.config_handler = ArchivistConfig()
        self.redis_con = RedisArchivist()
        self.has_run = self.get_has_run()

    def run(self):
        """run all startup checks"""
        print("run startup checks")
        self.set_lock()
        self.es_version_check()
        self.release_lock()
        self.sync_redis_state()
        self.set_redis_conf()
        ElasitIndexWrap().setup()
        self.make_folders()
        clear_dl_cache(self.config_handler.config)
        self.snapshot_check()
        self.ta_version_check()
        self.es_set_vid_type()
        self.expire_lock()

    def get_has_run(self):
        """validate if check has already executed"""
        return self.redis_con.get_message("startup_check")

    def set_lock(self):
        """set lock to avoid executing once per thread"""
        self.redis_con.set_message("startup_check", message={"status": True})

    def expire_lock(self):
        """startup checks run"""
        print("startup checks completed")
        message = {"status": True}
        self.redis_con.set_message("startup_check", message, expire=120)

    def sync_redis_state(self):
        """make sure redis gets new config.json values"""
        print("sync redis")
        self.config_handler.load_new_defaults()

    def set_redis_conf(self):
        """set conf values for redis"""
        self.redis_con.conn.config_set("timeout", 3600)

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
            os.makedirs(folder_path, exist_ok=True)

    def release_lock(self):
        """make sure there are no leftover locks set in redis"""
        all_locks = [
            "manual_import",
            "downloading",
            "dl_queue",
            "dl_queue_id",
            "reindex",
            "rescan",
            "run_backup",
        ]
        for lock in all_locks:
            response = self.redis_con.del_message(lock)
            if response:
                print("deleted leftover key from redis: " + lock)

    def snapshot_check(self):
        """setup snapshot config, create if needed"""
        app = self.config_handler.config["application"]
        if not app.get("enable_snapshot"):
            return

        ElasticSnapshot().setup()

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

    def ta_version_check(self):
        """remove key if updated now"""
        ReleaseVersion().is_updated()

    def es_set_vid_type(self):
        """
        update path 0.3.0 to 0.3.1, set default vid_type to video
        fix unidentified vids in unstable
        """
        index_list = ["ta_video", "ta_download"]
        data = {
            "query": {
                "bool": {
                    "should": [
                        {
                            "bool": {
                                "must_not": [{"exists": {"field": "vid_type"}}]
                            }
                        },
                        {"term": {"vid_type": {"value": "unknown"}}},
                    ]
                }
            },
            "script": {"source": "ctx._source['vid_type'] = 'videos'"},
        }

        for index_name in index_list:
            path = f"{index_name}/_update_by_query"
            response, _ = ElasticWrap(path).post(data=data)
            print(f"{index_name} vid_type index update ran: {response}")


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
