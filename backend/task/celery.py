"""initiate celery"""

import os

from celery import Celery
from common.src.env_settings import EnvironmentSettings


def con_parser():
    """allow for unix socket parsing"""
    redis_con = EnvironmentSettings.REDIS_CON
    if redis_con.startswith("unix://"):
        redis_con = EnvironmentSettings.REDIS_CON.replace(
            "unix://", "redis+socket://", 1
        )

    return redis_con


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
app = Celery(
    "tasks", broker=con_parser(), backend=con_parser(), result_extended=True
)
app.config_from_object(
    "django.conf:settings", namespace=EnvironmentSettings.REDIS_NAME_SPACE
)
app.autodiscover_tasks()
app.conf.timezone = EnvironmentSettings.TZ
