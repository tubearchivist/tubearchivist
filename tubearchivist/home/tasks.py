"""
Functionality:
- initiate celery app
- collect tasks
"""

import os

from celery import Celery, shared_task

from home.src.download import (
    PendingList,
    ChannelSubscription,
    VideoDownloader
)
from home.src.config import AppConfig


CONFIG = AppConfig().config
LIMIT_COUNT = CONFIG['downloads']['limit_count']
REDIS_HOST = CONFIG['application']['REDIS_HOST']

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'home.settings')
app = Celery('tasks', broker='redis://' + REDIS_HOST)
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


@shared_task
def update_subscribed():
    """ look for missing videos and add to pending """
    channel_handler = ChannelSubscription()
    missing_videos = channel_handler.find_missing()
    if missing_videos:
        pending_handler = PendingList()
        pending_handler.add_to_pending(missing_videos)


@shared_task
def download_pending():
    """ download latest pending videos """
    pending_handler = PendingList()
    pending_vids = pending_handler.get_all_pending()[0]
    pending = [i['youtube_id'] for i in pending_vids]
    pending.reverse()
    if LIMIT_COUNT:
        to_download = pending[:LIMIT_COUNT]
    else:
        to_download = pending
    if to_download:
        download_handler = VideoDownloader(to_download)
        download_handler.download_list()


@shared_task
def download_single(youtube_id):
    """ start download single video now """
    to_download = [youtube_id]
    download_handler = VideoDownloader(to_download)
    download_handler.download_list()


@shared_task
def extrac_dl(youtube_ids):
    """ parse list passed and add to pending """
    pending_handler = PendingList()
    missing_videos = pending_handler.parse_url_list(youtube_ids)
    pending_handler.add_to_pending(missing_videos)
