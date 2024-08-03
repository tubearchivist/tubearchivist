"""task model"""

from django.db import models
from django_celery_beat.models import PeriodicTask


class CustomPeriodicTask(PeriodicTask):
    """add custom metadata to task"""

    task_config = models.JSONField(default=dict)
