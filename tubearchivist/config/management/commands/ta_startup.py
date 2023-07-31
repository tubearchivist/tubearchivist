"""
Functionality:
- Application startup
- Apply migrations
"""

import os
from time import sleep

from django.core.management.base import BaseCommand, CommandError
from home.src.es.connect import ElasticWrap, IndexPaginate
from home.src.es.index_setup import ElasitIndexWrap
from home.src.es.snapshot import ElasticSnapshot
from home.src.index.video_streams import MediaStreamExtractor
from home.src.ta.config import AppConfig, ReleaseVersion
from home.src.ta.helper import clear_dl_cache
from home.src.ta.ta_redis import RedisArchivist
from home.src.ta.task_manager import TaskManager

TOPIC = """

#######################
#  Application Start  #
#######################

"""


class Command(BaseCommand):
    """command framework"""

    # pylint: disable=no-member

    def handle(self, *args, **options):
        """run all commands"""
        self.stdout.write(TOPIC)
        self._sync_redis_state()
        self._make_folders()
        self._release_locks()
        self._clear_tasks()
        self._clear_dl_cache()
        self._version_check()
        self._mig_index_setup()
        self._mig_snapshot_check()
        self._mig_set_streams()
        self._mig_set_autostart()

    def _sync_redis_state(self):
        """make sure redis gets new config.json values"""
        self.stdout.write("[1] set new config.json values")
        needs_update = AppConfig().load_new_defaults()
        if needs_update:
            self.stdout.write(
                self.style.SUCCESS("    ✓ new config values set")
            )
        else:
            self.stdout.write(self.style.SUCCESS("    no new config values"))

    def _make_folders(self):
        """make expected cache folders"""
        self.stdout.write("[2] create expected cache folders")
        folders = [
            "backup",
            "channels",
            "download",
            "import",
            "playlists",
            "videos",
        ]
        cache_dir = AppConfig().config["application"]["cache_dir"]
        for folder in folders:
            folder_path = os.path.join(cache_dir, folder)
            os.makedirs(folder_path, exist_ok=True)

        self.stdout.write(self.style.SUCCESS("    ✓ expected folders created"))

    def _release_locks(self):
        """make sure there are no leftover locks set in redis"""
        self.stdout.write("[3] clear leftover locks in redis")
        all_locks = [
            "dl_queue_id",
            "dl_queue",
            "downloading",
            "manual_import",
            "reindex",
            "rescan",
            "run_backup",
            "startup_check",
        ]

        redis_con = RedisArchivist()
        has_changed = False
        for lock in all_locks:
            if redis_con.del_message(lock):
                self.stdout.write(
                    self.style.SUCCESS(f"    ✓ cleared lock {lock}")
                )
                has_changed = True

        if not has_changed:
            self.stdout.write(self.style.SUCCESS("    no locks found"))

    def _clear_tasks(self):
        """clear tasks and messages"""
        self.stdout.write("[4] clear task leftovers")
        TaskManager().fail_pending()
        redis_con = RedisArchivist()
        to_delete = redis_con.list_keys("message:")
        if to_delete:
            for key in to_delete:
                redis_con.del_message(key)

            self.stdout.write(
                self.style.SUCCESS(f"    ✓ cleared {len(to_delete)} messages")
            )

    def _clear_dl_cache(self):
        """clear leftover files from dl cache"""
        self.stdout.write("[5] clear leftover files from dl cache")
        config = AppConfig().config
        leftover_files = clear_dl_cache(config)
        if leftover_files:
            self.stdout.write(
                self.style.SUCCESS(f"    ✓ cleared {leftover_files} files")
            )
        else:
            self.stdout.write(self.style.SUCCESS("    no files found"))

    def _version_check(self):
        """remove new release key if updated now"""
        self.stdout.write("[6] check for first run after update")
        new_version = ReleaseVersion().is_updated()
        if new_version:
            self.stdout.write(
                self.style.SUCCESS(f"    ✓ update to {new_version} completed")
            )
        else:
            self.stdout.write(self.style.SUCCESS("    no new update found"))

    def _mig_index_setup(self):
        """migration: validate index mappings"""
        self.stdout.write("[MIGRATION] validate index mappings")
        ElasitIndexWrap().setup()

    def _mig_snapshot_check(self):
        """migration setup snapshots"""
        self.stdout.write("[MIGRATION] setup snapshots")
        ElasticSnapshot().setup()

    def _mig_set_streams(self):
        """migration: update from 0.3.5 to 0.3.6, set streams and media_size"""
        self.stdout.write("[MIGRATION] index streams and media size")
        videos = AppConfig().config["application"]["videos"]
        data = {
            "query": {
                "bool": {"must_not": [{"exists": {"field": "streams"}}]}
            },
            "_source": ["media_url", "youtube_id"],
        }
        all_missing = IndexPaginate("ta_video", data).get_results()
        if not all_missing:
            self.stdout.write("    no videos need updating")
            return

        total = len(all_missing)
        for idx, missing in enumerate(all_missing):
            media_url = missing["media_url"]
            youtube_id = missing["youtube_id"]
            media_path = os.path.join(videos, media_url)
            if not os.path.exists(media_path):
                self.stdout.write(f"    file not found: {media_path}")
                self.stdout.write("    run file system rescan to fix")
                continue

            media = MediaStreamExtractor(media_path)
            vid_data = {
                "doc": {
                    "streams": media.extract_metadata(),
                    "media_size": media.get_file_size(),
                }
            }
            path = f"ta_video/_update/{youtube_id}"
            response, status_code = ElasticWrap(path).post(data=vid_data)
            if not status_code == 200:
                self.stdout.errors(
                    f"    update failed: {path}, {response}, {status_code}"
                )

            if idx % 100 == 0:
                self.stdout.write(f"    progress {idx}/{total}")

    def _mig_set_autostart(self):
        """migration: update from 0.3.5 to 0.3.6 set auto_start to false"""
        self.stdout.write("[MIGRATION] set default download auto_start")
        data = {
            "query": {
                "bool": {"must_not": [{"exists": {"field": "auto_start"}}]}
            },
            "script": {"source": "ctx._source['auto_start'] = false"},
        }
        path = "ta_download/_update_by_query"
        response, status_code = ElasticWrap(path).post(data=data)
        if status_code == 200:
            updated = response.get("updated", 0)
            if updated:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"    ✓ {updated} videos updated in ta_download"
                    )
                )
            else:
                self.stdout.write(
                    "    no videos needed updating in ta_download"
                )
            return

        message = "    🗙 ta_download auto_start update failed"
        self.stdout.write(self.style.ERROR(message))
        self.stdout.write(response)
        sleep(60)
        raise CommandError(message)
