"""start celery app"""

from __future__ import absolute_import, unicode_literals

from task.celery import app as celery_app

__all__ = ("celery_app",)
