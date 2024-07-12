"""
Functionality:
- Handle scheduler config update
"""

from datetime import datetime

from django.utils import dateformat
from django_celery_beat.models import CrontabSchedule
from home.models import CustomPeriodicTask
from home.src.ta.config import AppConfig
from home.src.ta.settings import EnvironmentSettings
from home.src.ta.task_config import TASK_CONFIG


class ScheduleBuilder:
    """build schedule dicts for beat"""

    SCHEDULES = {
        "update_subscribed": "0 8 *",
        "download_pending": "0 16 *",
        "check_reindex": "0 12 *",
        "thumbnail_check": "0 17 *",
        "run_backup": "0 18 0",
        "version_check": "0 11 *",
    }
    CONFIG = {
        "check_reindex_days": "check_reindex",
        "run_backup_rotate": "run_backup",
        "update_subscribed_notify": "update_subscribed",
        "download_pending_notify": "download_pending",
        "check_reindex_notify": "check_reindex",
    }
    MSG = "message:setting"

    def __init__(self):
        self.config = AppConfig().config

    def update_schedule_conf(self, form_post):
        """process form post, schedules need to be validated before"""
        for key, value in form_post.items():
            if not value:
                continue

            if key in self.SCHEDULES:
                if value == "auto":
                    value = self.SCHEDULES.get(key)

                _ = self.get_set_task(key, value)
                continue

            if key in self.CONFIG:
                self.set_config(key, value)

    def get_set_task(self, task_name, schedule=False):
        """get task"""
        try:
            task = CustomPeriodicTask.objects.get(name=task_name)
        except CustomPeriodicTask.DoesNotExist:
            description = TASK_CONFIG[task_name].get("title")
            task = CustomPeriodicTask(
                name=task_name,
                task=task_name,
                description=description,
            )

        if schedule:
            task_crontab = self.get_set_cron_tab(schedule)
            task.crontab = task_crontab
            task.last_run_at = dateformat.make_aware(datetime.now())
            task.save()

        return task

    @staticmethod
    def get_set_cron_tab(schedule):
        """needs to be validated before"""
        kwargs = dict(zip(["minute", "hour", "day_of_week"], schedule.split()))
        kwargs.update({"timezone": EnvironmentSettings.TZ})
        crontab, _ = CrontabSchedule.objects.get_or_create(**kwargs)

        return crontab

    def set_config(self, key, value):
        """set task_config"""
        task_name = self.CONFIG.get(key)
        if not task_name:
            raise ValueError("invalid config key")

        task = CustomPeriodicTask.objects.get(name=task_name)
        config_key = key.split(f"{task_name}_")[-1]
        task.task_config.update({config_key: value})
        task.save()
