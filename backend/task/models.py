"""task model"""

from django.db import models
from django_celery_beat.models import PeriodicTask, cronexp


class CustomPeriodicTask(PeriodicTask):
    """add custom metadata to task"""

    task_config = models.JSONField(default=dict)

    @property
    def schedule_parsed(self):
        """parse schedule"""
        minute = cronexp(self.crontab.minute)
        hour = cronexp(self.crontab.hour)
        day_of_week = cronexp(self.crontab.day_of_week)

        return f"{minute} {hour} {day_of_week}"
