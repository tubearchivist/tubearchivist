"""initiate celery"""

import os

from celery import Celery
from home.src.ta.settings import EnvironmentSettings

REDIS_HOST = EnvironmentSettings.REDIS_HOST
REDIS_PORT = EnvironmentSettings.REDIS_PORT

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
app = Celery(
    "tasks",
    broker=f"redis://{REDIS_HOST}:{REDIS_PORT}",
    backend=f"redis://{REDIS_HOST}:{REDIS_PORT}",
    result_extended=True,
)
app.config_from_object(
    "django.conf:settings", namespace=EnvironmentSettings.REDIS_NAME_SPACE
)
app.autodiscover_tasks()
app.conf.timezone = EnvironmentSettings.TZ
