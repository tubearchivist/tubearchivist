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
from home.src.reindex import reindex_old_documents, ManualImport
from home.src.index_management import backup_all_indexes
from home.src.helper import get_lock


CONFIG = AppConfig().config
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
    # check if reindex is needed
    check_reindex.delay()


@shared_task
def download_pending():
    """ download latest pending videos """
    pending_handler = PendingList()
    pending_vids = pending_handler.get_all_pending()[0]
    to_download = [i['youtube_id'] for i in pending_vids]
    to_download.reverse()
    if to_download:
        download_handler = VideoDownloader(to_download)
        download_handler.download_list()


@shared_task
def download_single(youtube_id):
    """ start download single video now """
    download_handler = VideoDownloader([youtube_id])
    download_handler.download_list()


@shared_task
def extrac_dl(youtube_ids):
    """ parse list passed and add to pending """
    pending_handler = PendingList()
    missing_videos = pending_handler.parse_url_list(youtube_ids)
    pending_handler.add_to_pending(missing_videos)


@shared_task
def check_reindex():
    """ run the reindex main command """
    reindex_old_documents()


@shared_task
def run_manual_import():
    """ called from settings page, to go through import folder """

    print('starting media file import')
    have_lock = False
    my_lock = get_lock('manual_import')

    try:
        have_lock = my_lock.acquire(blocking=False)
        if have_lock:
            import_handler = ManualImport()
            if import_handler.identified:
                import_handler.process_import()
        else:
            print("Did not acquire lock form import.")

    finally:
        if have_lock:
            my_lock.release()


@shared_task
def run_backup():
    """ called from settings page, dump backup to zip file """
    backup_all_indexes()
    print('backup finished')
