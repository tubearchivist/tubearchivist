"""
Functionality:
- Application startup
- Apply migrations
"""

import os
from time import sleep

from django.core.management.base import BaseCommand, CommandError
from home.src.es.connect import ElasticWrap
from home.src.es.index_setup import ElasitIndexWrap
from home.src.es.snapshot import ElasticSnapshot
from home.src.ta.config import AppConfig, ReleaseVersion
from home.src.ta.helper import clear_dl_cache
from home.src.ta.settings import EnvironmentSettings
from home.src.ta.ta_redis import RedisArchivist
from home.src.ta.task_manager import TaskManager
from home.src.ta.users import UserConfig

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
        self._clear_redis_keys()
        self._clear_tasks()
        self._clear_dl_cache()
        self._mig_clear_failed_versioncheck()
        self._version_check()
        self._mig_index_setup()
        self._mig_snapshot_check()
        self._mig_move_users_to_es()
        self._mig_custom_playlist()

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
        cache_dir = EnvironmentSettings.CACHE_DIR
        for folder in folders:
            folder_path = os.path.join(cache_dir, folder)
            os.makedirs(folder_path, exist_ok=True)

        self.stdout.write(self.style.SUCCESS("    ✓ expected folders created"))

    def _clear_redis_keys(self):
        """make sure there are no leftover locks or keys set in redis"""
        self.stdout.write("[3] clear leftover keys in redis")
        all_keys = [
            "dl_queue_id",
            "dl_queue",
            "downloading",
            "manual_import",
            "reindex",
            "rescan",
            "run_backup",
            "startup_check",
            "reindex:ta_video",
            "reindex:ta_channel",
            "reindex:ta_playlist",
        ]

        redis_con = RedisArchivist()
        has_changed = False
        for key in all_keys:
            if redis_con.del_message(key):
                self.stdout.write(
                    self.style.SUCCESS(f"    ✓ cleared key {key}")
                )
                has_changed = True

        if not has_changed:
            self.stdout.write(self.style.SUCCESS("    no keys found"))

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
        leftover_files = clear_dl_cache(EnvironmentSettings.CACHE_DIR)
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

    def _mig_clear_failed_versioncheck(self):
        """hotfix for v0.4.5, clearing faulty versioncheck"""
        ReleaseVersion().clear_fail()

    def _mig_move_users_to_es(self):  # noqa: C901
        """migration: update from 0.4.1 to 0.4.2 move user config to ES"""
        self.stdout.write("[MIGRATION] move user configuration to ES")
        redis = RedisArchivist()

        # 1: Find all users in Redis
        users = {i.split(":")[0] for i in redis.list_keys("[0-9]*:")}
        if not users:
            self.stdout.write("    no users needed migrating to ES")
            return

        # 2: Write all Redis user settings to ES
        # 3: Remove user settings from Redis
        try:
            for user in users:
                new_conf = UserConfig(user)

                stylesheet_key = f"{user}:color"
                stylesheet = redis.get_message(stylesheet_key).get("status")
                if stylesheet:
                    new_conf.set_value("stylesheet", stylesheet)
                    redis.del_message(stylesheet_key)

                sort_by_key = f"{user}:sort_by"
                sort_by = redis.get_message(sort_by_key).get("status")
                if sort_by:
                    new_conf.set_value("sort_by", sort_by)
                    redis.del_message(sort_by_key)

                page_size_key = f"{user}:page_size"
                page_size = redis.get_message(page_size_key).get("status")
                if page_size:
                    new_conf.set_value("page_size", page_size)
                    redis.del_message(page_size_key)

                sort_order_key = f"{user}:sort_order"
                sort_order = redis.get_message(sort_order_key).get("status")
                if sort_order:
                    new_conf.set_value("sort_order", sort_order)
                    redis.del_message(sort_order_key)

                grid_items_key = f"{user}:grid_items"
                grid_items = redis.get_message(grid_items_key).get("status")
                if grid_items:
                    new_conf.set_value("grid_items", grid_items)
                    redis.del_message(grid_items_key)

                hide_watch_key = f"{user}:hide_watched"
                hide_watch = redis.get_message(hide_watch_key).get("status")
                if hide_watch:
                    new_conf.set_value("hide_watched", hide_watch)
                    redis.del_message(hide_watch_key)

                ignore_only_key = f"{user}:show_ignored_only"
                ignore_only = redis.get_message(ignore_only_key).get("status")
                if ignore_only:
                    new_conf.set_value("show_ignored_only", ignore_only)
                    redis.del_message(ignore_only_key)

                subed_only_key = f"{user}:show_subed_only"
                subed_only = redis.get_message(subed_only_key).get("status")
                if subed_only:
                    new_conf.set_value("show_subed_only", subed_only)
                    redis.del_message(subed_only_key)

                for view in ["channel", "playlist", "home", "downloads"]:
                    view_key = f"{user}:view:{view}"
                    view_style = redis.get_message(view_key).get("status")
                    if view_style:
                        new_conf.set_value(f"view_style_{view}", view_style)
                        redis.del_message(view_key)

                self.stdout.write(
                    self.style.SUCCESS(
                        f"    ✓ Settings for user '{user}' migrated to ES"
                    )
                )
        except Exception as err:
            message = "    🗙 user migration to ES failed"
            self.stdout.write(self.style.ERROR(message))
            self.stdout.write(self.style.ERROR(err))
            sleep(60)
            raise CommandError(message) from err
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    "    ✓ Settings for all users migrated to ES"
                )
            )

    def _mig_custom_playlist(self):
        """migration for custom playlist"""
        self.stdout.write("[MIGRATION] custom playlist")
        data = {
            "query": {
                "bool": {"must_not": [{"exists": {"field": "playlist_type"}}]}
            },
            "script": {"source": "ctx._source['playlist_type'] = 'regular'"},
        }
        path = "ta_playlist/_update_by_query"
        response, status_code = ElasticWrap(path).post(data=data)
        if status_code == 200:
            updated = response.get("updated", 0)
            if updated:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"    ✓ {updated} playlist_type updated in ta_playlist"
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        "    no playlist_type needed updating in ta_playlist"
                    )
                )
            return

        message = "    🗙 ta_playlist playlist_type update failed"
        self.stdout.write(self.style.ERROR(message))
        self.stdout.write(response)
        sleep(60)
        raise CommandError(message)
