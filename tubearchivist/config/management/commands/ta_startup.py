"""
Functionality:
- Application startup
- Apply migrations
"""

import os

from django.core.management.base import BaseCommand, CommandError
from home.src.es.connect import ElasticWrap
from home.src.es.index_setup import ElasitIndexWrap
from home.src.es.snapshot import ElasticSnapshot
from home.src.ta.config import AppConfig, ReleaseVersion
from home.src.ta.helper import clear_dl_cache
from home.src.ta.ta_redis import RedisArchivist

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
        self._clear_dl_cache()
        self._version_check()
        self._mig_index_setup()
        self._mig_snapshot_check()
        self._mig_set_vid_type()

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

    def _clear_dl_cache(self):
        """clear leftover files from dl cache"""
        self.stdout.write("[4] clear leftover files from dl cache")
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
        self.stdout.write("[5] check for first run after update")
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

    def _mig_set_vid_type(self):
        """migration: update 0.3.0 to 0.3.1 set vid_type default"""
        self.stdout.write("[MIGRATION] set default vid_type")
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
            response, status_code = ElasticWrap(path).post(data=data)
            if status_code == 200:
                updated = response.get("updated", 0)
                if not updated:
                    self.stdout.write(
                        f"    no videos needed updating in {index_name}"
                    )
                    continue

                self.stdout.write(
                    self.style.SUCCESS(
                        f"    ✓ {updated} videos updated in {index_name}"
                    )
                )
            else:
                message = f"    🗙 {index_name} vid_type update failed"
                self.stdout.write(self.style.ERROR(message))
                self.stdout.write(response)
                raise CommandError(message)
