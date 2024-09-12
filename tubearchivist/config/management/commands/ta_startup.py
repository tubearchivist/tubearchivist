"""
Functionality:
- Application startup
- Apply migrations
"""

import os
from datetime import datetime
from random import randint
from time import sleep

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import dateformat
from django_celery_beat.models import CrontabSchedule, PeriodicTasks
from home.models import CustomPeriodicTask
from home.src.es.connect import ElasticWrap
from home.src.es.index_setup import ElasitIndexWrap
from home.src.es.snapshot import ElasticSnapshot
from home.src.ta.config import AppConfig, ReleaseVersion
from home.src.ta.config_schedule import ScheduleBuilder
from home.src.ta.helper import clear_dl_cache
from home.src.ta.notify import Notifications
from home.src.ta.settings import EnvironmentSettings
from home.src.ta.ta_redis import RedisArchivist
from home.src.ta.task_config import TASK_CONFIG
from home.src.ta.task_manager import TaskManager
from home.tasks import version_check

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
        self._version_check()
        self._mig_index_setup()
        self._mig_snapshot_check()
        self._mig_schedule_store()
        self._mig_custom_playlist()
        self._mig_add_missing_timestamp()
        self._create_default_schedules()
        self._update_schedule_tz()

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

        version_task = CustomPeriodicTask.objects.filter(name="version_check")
        if not version_task.exists():
            return

        if not version_task.first().last_run_at:
            self.style.SUCCESS("    ✓ send initial version check task")
            version_check.delay()

    def _mig_index_setup(self):
        """migration: validate index mappings"""
        self.stdout.write("[MIGRATION] validate index mappings")
        ElasitIndexWrap().setup()

    def _mig_snapshot_check(self):
        """migration setup snapshots"""
        self.stdout.write("[MIGRATION] setup snapshots")
        ElasticSnapshot().setup()

    def _mig_schedule_store(self):
        """
        update from 0.4.7 to 0.4.8
        migrate schedule task store to CustomCronSchedule
        """
        self.stdout.write("[MIGRATION] migrate schedule store")
        config = AppConfig().config
        current_schedules = config.get("scheduler")
        if not current_schedules:
            self.stdout.write(
                self.style.SUCCESS("    no schedules to migrate")
            )
            return

        self._mig_update_subscribed(current_schedules)
        self._mig_download_pending(current_schedules)
        self._mig_check_reindex(current_schedules)
        self._mig_thumbnail_check(current_schedules)
        self._mig_run_backup(current_schedules)
        self._mig_version_check()

        del config["scheduler"]
        RedisArchivist().set_message("config", config, save=True)

    def _mig_update_subscribed(self, current_schedules):
        """create update_subscribed schedule"""
        task_name = "update_subscribed"
        update_subscribed_schedule = current_schedules.get(task_name)
        if update_subscribed_schedule:
            self._create_task(task_name, update_subscribed_schedule)

        self._create_notifications(task_name, current_schedules)

    def _mig_download_pending(self, current_schedules):
        """create download_pending schedule"""
        task_name = "download_pending"
        download_pending_schedule = current_schedules.get(task_name)
        if download_pending_schedule:
            self._create_task(task_name, download_pending_schedule)

        self._create_notifications(task_name, current_schedules)

    def _mig_check_reindex(self, current_schedules):
        """create check_reindex schedule"""
        task_name = "check_reindex"
        check_reindex_schedule = current_schedules.get(task_name)
        if check_reindex_schedule:
            task_config = {}
            days = current_schedules.get("check_reindex_days")
            if days:
                task_config.update({"days": days})

            self._create_task(
                task_name,
                check_reindex_schedule,
                task_config=task_config,
            )

        self._create_notifications(task_name, current_schedules)

    def _mig_thumbnail_check(self, current_schedules):
        """create thumbnail_check schedule"""
        thumbnail_check_schedule = current_schedules.get("thumbnail_check")
        if thumbnail_check_schedule:
            self._create_task("thumbnail_check", thumbnail_check_schedule)

    def _mig_run_backup(self, current_schedules):
        """create run_backup schedule"""
        run_backup_schedule = current_schedules.get("run_backup")
        if run_backup_schedule:
            task_config = False
            rotate = current_schedules.get("run_backup_rotate")
            if rotate:
                task_config = {"rotate": rotate}

            self._create_task(
                "run_backup", run_backup_schedule, task_config=task_config
            )

    def _mig_version_check(self):
        """create version_check schedule"""
        version_check_schedule = {
            "minute": randint(0, 59),
            "hour": randint(0, 23),
            "day_of_week": "*",
        }
        self._create_task("version_check", version_check_schedule)

    def _create_task(self, task_name, schedule, task_config=False):
        """create task"""
        description = TASK_CONFIG[task_name].get("title")
        schedule, _ = CrontabSchedule.objects.get_or_create(**schedule)
        schedule.timezone = settings.TIME_ZONE
        schedule.save()

        task, _ = CustomPeriodicTask.objects.get_or_create(
            crontab=schedule,
            name=task_name,
            description=description,
            task=task_name,
        )
        if task_config:
            task.task_config = task_config
            task.save()

        self.stdout.write(
            self.style.SUCCESS(f"    ✓ new task created: '{task}'")
        )

    def _create_notifications(self, task_name, current_schedules):
        """migrate notifications of task"""
        notifications = current_schedules.get(f"{task_name}_notify")
        if not notifications:
            return

        urls = [i.strip() for i in notifications.split()]
        if not urls:
            return

        self.stdout.write(
            self.style.SUCCESS(f"    ✓ migrate notifications: '{urls}'")
        )
        handler = Notifications(task_name)
        for url in urls:
            handler.add_url(url)

    def _mig_custom_playlist(self):
        """add playlist_type for migration from v0.4.6 to v0.4.7"""
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

    def _mig_add_missing_timestamp(self) -> None:
        """
        add missing timestamp for versioncheck
        migrate from v0.4.8 to v0.4.9
        """
        version_tasks = CustomPeriodicTask.objects.filter(name="version_check")
        if not version_tasks.exists():
            return

        version_task = version_tasks.first()
        if not version_task.last_run_at:
            self.style.SUCCESS("    ✓ send initial version check task")
            version_check.delay()
            version_task.last_run_at = dateformat.make_aware(datetime.now())
            version_task.save()

    def _create_default_schedules(self) -> None:
        """
        create default schedules for new installations
        needs to be called after _mig_schedule_store
        """
        self.stdout.write("[7] create initial schedules")
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
