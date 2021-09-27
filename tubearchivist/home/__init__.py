""" handle celery startup """

from .tasks import app as celery_app

__all__ = ("celery_app",)
