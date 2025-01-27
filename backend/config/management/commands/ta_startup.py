"""
Functionality:
- Application startup
- Apply migrations
"""

import os
from datetime import datetime
from random import randint
from time import sleep

from appsettings.src.config import AppConfig, ReleaseVersion
from appsettings.src.index_setup import ElasitIndexWrap
from appsettings.src.snapshot import ElasticSnapshot
from common.src.env_settings import EnvironmentSettings
from common.src.es_connect import ElasticWrap
from common.src.helper import clear_dl_cache
from common.src.ta_redis import RedisArchivist
from django.core.management.base import BaseCommand, CommandError
from django.utils import dateformat
from django_celery_beat.models import CrontabSchedule, PeriodicTasks
from redis.exceptions import ResponseError
from task.models import CustomPeriodicTask
from task.src.config_schedule import ScheduleBuilder
from task.src.task_manager import TaskManager
from task.tasks import version_check

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
        self._mig_app_settings()
        self._make_folders()
        self._clear_redis_keys()
        self._clear_tasks()
        self._clear_dl_cache()
        self._version_check()
        self._index_setup()
        self._snapshot_check()
        self._create_default_schedules()
        self._update_schedule_tz()
        self._init_app_config()

    def _mig_app_settings(self) -> None:
        """update from v0.4.13 to v0.5.0, migrate application settings"""
        self.stdout.write("[MIGRATION] move appconfig to ES")
        try:
            config = RedisArchivist().get_message("config")
        except ResponseError:
            self.stdout.write(
                self.style.SUCCESS("    Redis does not support JSON decoding")
            )
            return

        if not config:
            self.stdout.write(
                self.style.SUCCESS("    no config values to migrate")
            )
            return

        path = "ta_config/_doc/appsettings"
        response, status_code = ElasticWrap(path).post(config)

        if status_code in [200, 201]:
            self.stdout.write(
                self.style.SUCCESS("    ✓ migrated appconfig to ES")
            )
            RedisArchivist().del_message("config")
            return

        message = "    🗙 failed to migrate app config"
        self.stdout.write(self.style.ERROR(message))
        self.stdout.write(response)
        sleep(60)
        raise CommandError(message)

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

        version_task = CustomPeriodicTask.objects.filter(name="version_check")
        if not version_task.exists():
            return

        if not version_task.first().last_run_at:
            self.style.SUCCESS("    ✓ send initial version check task")
            version_check.delay()

    def _index_setup(self):
        """migration: validate index mappings"""
        self.stdout.write("[7] validate index mappings")
        ElasitIndexWrap().setup()

    def _snapshot_check(self):
        """migration setup snapshots"""
        self.stdout.write("[8] setup snapshots")
        ElasticSnapshot().setup()

    def _create_default_schedules(self) -> None:
        """create default schedules for new installations"""
        self.stdout.write("[9] create initial schedules")
        init_has_run = CustomPeriodicTask.objects.filter(
            name="version_check"
        ).exists()

        if init_has_run:
            self.stdout.write(
                self.style.SUCCESS(
                    "    schedule init already done, skipping..."
                )
            )
            return

        builder = ScheduleBuilder()
        check_reindex = builder.get_set_task(
            "check_reindex", schedule=builder.SCHEDULES["check_reindex"]
        )
        check_reindex.task_config.update({"days": 90})
        check_reindex.last_run_at = dateformat.make_aware(datetime.now())
        check_reindex.save()
        self.stdout.write(
            self.style.SUCCESS(
                f"    ✓ created new default schedule: {check_reindex}"
            )
        )

        thumbnail_check = builder.get_set_task(
            "thumbnail_check", schedule=builder.SCHEDULES["thumbnail_check"]
        )
        thumbnail_check.last_run_at = dateformat.make_aware(datetime.now())
        thumbnail_check.save()
        self.stdout.write(
            self.style.SUCCESS(
                f"    ✓ created new default schedule: {thumbnail_check}"
            )
        )
        daily_random = f"{randint(0, 59)} {randint(0, 23)} *"
        version_check_task = builder.get_set_task(
            "version_check", schedule=daily_random
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"    ✓ created new default schedule: {version_check_task}"
            )
        )
        self.stdout.write(
            self.style.SUCCESS("    ✓ all default schedules created")
        )

    def _update_schedule_tz(self) -> None:
        """update timezone for Schedule instances"""
        self.stdout.write("[10] validate schedules TZ")
        tz = EnvironmentSettings.TZ
        to_update = CrontabSchedule.objects.exclude(timezone=tz)

        if not to_update.exists():
            self.stdout.write(
                self.style.SUCCESS("    all schedules have correct TZ")
            )
            return

        updated = to_update.update(timezone=tz)
        self.stdout.write(
            self.style.SUCCESS(f"    ✓ updated {updated} schedules to {tz}.")
        )
        PeriodicTasks.update_changed()

    def _init_app_config(self) -> None:
        """init default app config to ES"""
        self.stdout.write("[11] Check AppConfig")
        try:
            _ = AppConfig().config
            self.stdout.write(
                self.style.SUCCESS("    skip completed appsettings init")
            )
            updated_defaults = AppConfig().add_new_defaults()
            for new_default in updated_defaults:
                self.stdout.write(
                    self.style.SUCCESS(f"    added new default: {new_default}")
                )

        except ValueError:
            handler = AppConfig.__new__(AppConfig)
            _, status_code = handler.sync_defaults()
            self.stdout.write(
                self.style.SUCCESS("    ✓ Created default appsettings.")
            )
            self.stdout.write(
                self.style.SUCCESS(f"      Status code: {status_code}")
            )
