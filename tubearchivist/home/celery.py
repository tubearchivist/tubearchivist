"""initiate celery"""

import os

from celery import Celery
from home.src.ta.settings import EnvironmentSettings

REDIS_HOST = EnvironmentSettings.REDIS_HOST
REDIS_PORT = EnvironmentSettings.REDIS_PORT
REDIS_DB = EnvironmentSettings.REDIS_DB

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
app = Celery(
    "tasks",
    broker=f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}",
    backend=f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}",
    result_extended=True,
)
app.config_from_object(
    "django.conf:settings", namespace=EnvironmentSettings.REDIS_NAME_SPACE
)
app.autodiscover_tasks()
app.conf.timezone = EnvironmentSettings.TZ
