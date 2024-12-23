"""initiate celery"""

import os

from celery import Celery
from common.src.env_settings import EnvironmentSettings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
app = Celery(
    "tasks",
    broker=EnvironmentSettings.REDIS_CON,
    backend=EnvironmentSettings.REDIS_CON,
    result_extended=True,
)
app.config_from_object(
    "django.conf:settings", namespace=EnvironmentSettings.REDIS_NAME_SPACE
)
app.autodiscover_tasks()
app.conf.timezone = EnvironmentSettings.TZ
