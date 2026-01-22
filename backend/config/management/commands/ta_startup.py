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
from appsettings.src.index_setup import ElasticIndexWrap
from appsettings.src.snapshot import ElasticSnapshot
from channel.src.index import YoutubeChannel
from common.src.env_settings import EnvironmentSettings
from common.src.es_connect import ElasticWrap, IndexPaginate
from common.src.helper import clear_dl_cache, get_channels
from common.src.ta_redis import RedisArchivist
from django.core.management.base import BaseCommand, CommandError
from django.utils import dateformat
from django_celery_beat.models import CrontabSchedule, PeriodicTasks
from task.models import CustomPeriodicTask
from task.src.config_schedule import ScheduleBuilder
from task.src.task_manager import TaskManager
from task.tasks import version_check
from video.src.constants import VideoTypeEnum
from video.src.index import YoutubeVideo

TOPIC = """

#######################
#  Application Start  #
#######################

"""


class Command(BaseCommand):
    """command framework"""

    def handle(self, *args, **options):
        """run all commands"""
        self.stdout.write(TOPIC)
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
        self._set_ta_startup_time()
        self._mig_add_default_playlist_sort()
        self._mig_set_channel_tabs()
        self._mig_set_video_channel_tabs()
        self._mig_fix_playlist_description()
        self._mig_fix_missing_stats()
        self._mig_fix_channel_art_types()
        self._mig_fix_channel_description()
        self._mig_fix_video_description()

    def _make_folders(self):
        """make expected cache folders"""
        self.stdout.write("[1] create expected cache folders")
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
        self.stdout.write("[2] clear leftover keys in redis")
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
        self.stdout.write("[3] clear task leftovers")
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
        self.stdout.write("[4] clear leftover files from dl cache")
        leftover_files = clear_dl_cache(EnvironmentSettings.CACHE_DIR)
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

        version_task = CustomPeriodicTask.objects.filter(name="version_check")
        if not version_task.exists():
            return

        if not version_task.first().last_run_at:
            self.style.SUCCESS("    ✓ send initial version check task")
            version_check.delay()

    def _index_setup(self):
        """migration: validate index mappings"""
        self.stdout.write("[6] validate index mappings")
        ElasticIndexWrap().setup()

    def _snapshot_check(self):
        """migration setup snapshots"""
        self.stdout.write("[7] setup snapshots")
        ElasticSnapshot().setup()

    def _create_default_schedules(self) -> None:
        """create default schedules for new installations"""
        self.stdout.write("[8] create initial schedules")
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
        self.stdout.write("[9] validate schedules TZ")
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
        self.stdout.write("[10] Check AppConfig")
        response, status_code = ElasticWrap("ta_config/_doc/appsettings").get()
        if status_code in [200, 201]:
            self.stdout.write(
                self.style.SUCCESS("    skip completed appsettings init")
            )
            updated_defaults = AppConfig().add_new_defaults()
            for new_default in updated_defaults:
                self.stdout.write(
                    self.style.SUCCESS(f"    added new default: {new_default}")
                )

            return

        if status_code != 404:
            message = "    🗙 ta_config index lookup failed"
            self.stdout.write(self.style.ERROR(message))
            self.stdout.write(response)
            sleep(60)
            raise CommandError(message)

        handler = AppConfig.__new__(AppConfig)
        _, status_code = handler.sync_defaults()
        self.stdout.write(
            self.style.SUCCESS("    ✓ Created default appsettings.")
        )
        self.stdout.write(
            self.style.SUCCESS(f"      Status code: {status_code}")
        )

    def _set_ta_startup_time(self) -> None:
        """set startup time to trigger frontend refresh, threadsafe"""
        self.stdout.write("[11] Set startup timestamp")
        message = str(int(datetime.now().timestamp() // 10 * 10))
        RedisArchivist().set_message(
            "STARTTIMESTAMP", message=message, save=True
        )
        self.stdout.write(
            self.style.SUCCESS(f"    ✓ set timestamp to {message}.")
        )

    def _mig_add_default_playlist_sort(self) -> None:
        """migrate from 0.5.4 to 0.5.5 set default playlist sortorder"""
        self._run_migration(
            index_name="ta_playlist",
            desc="set default playlist sort order",
            query={
                "bool": {
                    "must_not": [{"exists": {"field": "playlist_sort_order"}}]
                }
            },
            script={
                "source": "ctx._source.playlist_sort_order = 'top'",
                "lang": "painless",
            },
        )

    def _mig_set_channel_tabs(self) -> None:
        """migrate from 0.5.4 to 0.5.5 set initial channel tabs"""
        tabs = VideoTypeEnum.values_known()
        self._run_migration(
            index_name="ta_channel",
            desc="set default channel_tabs in channel index",
            query={
                "bool": {"must_not": [{"exists": {"field": "channel_tabs"}}]}
            },
            script={
                "source": f"ctx._source.channel_tabs = {tabs}",
                "lang": "painless",
            },
        )

    def _mig_set_video_channel_tabs(self) -> None:
        """migrate from 0.5.4 to 0.5.5 set initial video channel tabs"""
        tabs = VideoTypeEnum.values_known()
        self._run_migration(
            index_name="ta_video",
            desc="set default channel_tabs for videos",
            query={
                "bool": {
                    "must_not": [{"exists": {"field": "channel.channel_tabs"}}]
                }
            },
            script={
                "source": f"ctx._source.channel.channel_tabs = {tabs}",
                "lang": "painless",
            },
        )

    def _mig_fix_playlist_description(self) -> None:
        """migrate from 0.5.8 to 0.5.9 fix playlist desc null data type"""
        self._run_migration(
            index_name="ta_playlist",
            desc="fix playlist description data type",
            query={"term": {"playlist_description": {"value": False}}},
            script={
                "source": "ctx._source.remove('playlist_description')",
                "lang": "painless",
            },
        )

    def _mig_fix_missing_stats(self) -> None:
        """migrate from 0.5.8 to 0.5.9, fix missing stats values"""
        fields = [
            "like_count",
            "average_rating",
            "view_count",
            "dislike_count",
        ]
        for field in fields:
            self._run_migration(
                index_name="ta_video",
                desc=f"fix missing stats field {field}",
                query={
                    "bool": {
                        "must_not": [{"exists": {"field": f"stats.{field}"}}]
                    }
                },
                script={
                    "source": f"ctx._source.stats.{field} = 0",
                    "lang": "painless",
                },
            )

    def _mig_fix_channel_art_types(self) -> None:
        """migrate from 0.5.8 to 0.5.9, fix channel artwork types"""
        fields = [
            "channel_banner_url",
            "channel_thumb_url",
            "channel_tvart_url",
        ]
        for field in fields:
            self._run_migration(
                index_name="ta_channel",
                desc=f"fix missing data type for field {field}",
                query={"term": {field: {"value": False}}},
                script={
                    "source": f"ctx._source.remove('{field}')",
                    "lang": "painless",
                },
            )
            self._run_migration(
                index_name="ta_video",
                desc=f"fix missing data type for field channel.{field}",
                query={"term": {f"channel.{field}": {"value": False}}},
                script={
                    "source": f"ctx._source.remove('channel.{field}')",
                    "lang": "painless",
                },
            )

    def _mig_fix_channel_description(self) -> None:
        """migrate from 0.5.8 to 0.5.9, fix channel desc null value"""
        desc = "fix channel description null value"
        self.stdout.write(f"[MIGRATION] run {desc}")
        channels = get_channels(
            subscribed_only=False, source=["channel_description", "channel_id"]
        )
        counter = 0
        for channel_response in channels:
            if not channel_response.get("channel_description") == "":
                continue

            channel = YoutubeChannel(youtube_id=channel_response["channel_id"])
            channel.get_from_es()
            channel.json_data.pop("channel_description")
            channel.upload_to_es()
            channel.sync_to_videos()
            counter += 1

        if counter:
            suc_msg = f"    ✓ updated {counter} channels with videos"
            self.stdout.write(self.style.SUCCESS(suc_msg))
        else:
            noop_msg = "    no items needed updating"
            self.stdout.write(self.style.SUCCESS(noop_msg))

    def _mig_fix_video_description(self) -> None:
        """migrate from 0.5.8 to 0.5.9, fix video desc null value"""
        desc = "fix video description null value"
        self.stdout.write(f"[MIGRATION] run {desc}")

        data = {"_source": ["youtube_id", "description"]}
        videos = IndexPaginate("ta_video", data=data).get_results()

        counter = 0
        for video_response in videos:
            if not video_response.get("description") == "":
                continue

            video = YoutubeVideo(youtube_id=video_response["youtube_id"])
            video.get_from_es()
            video.json_data.pop("description")
            video.upload_to_es()

            counter += 1

        if counter:
            suc_msg = f"    ✓ updated {counter} videos"
            self.stdout.write(self.style.SUCCESS(suc_msg))
        else:
            noop_msg = "    no items needed updating"
            self.stdout.write(self.style.SUCCESS(noop_msg))

    def _run_migration(
        self, index_name: str, desc: str, query: dict, script: dict
    ):
        """run migration"""
        self.stdout.write(f"[MIGRATION] run {desc}")
        path = f"{index_name}/_update_by_query"
        data = {"query": query, "script": script}
        response, status_code = ElasticWrap(path).post(data)
        if status_code in [200, 201]:
            updated = response.get("updated")
            if updated:
                suc_msg = f"    ✓ updated {updated} docs in {index_name}"
                self.stdout.write(self.style.SUCCESS(suc_msg))
            else:
                noop_msg = f"    no items in {index_name} need updating"
                self.stdout.write(self.style.SUCCESS(noop_msg))
            return

        message = f"    🗙 failed to run {desc} on index {index_name}"
        self.stdout.write(self.style.ERROR(message))
        self.stdout.write(response)
        sleep(60)
        raise CommandError(message)
