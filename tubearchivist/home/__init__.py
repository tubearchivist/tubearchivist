""" handle startup """

import os

from home.src.config import AppConfig
from home.src.helper import set_message
from home.src.index_management import index_check

from .tasks import app as celery_app


def sync_redis_state():
    """ make sure redis gets the config.json values """
    print('sync redis')
    config = AppConfig().config
    sort_order = config['archive']['sort']
    set_message('sort_order', sort_order, expire=False)
    hide_watched = bool(int(config['archive']['hide_watched']))
    set_message('hide_watched', hide_watched, expire=False)
    show_subed_only = bool(int(config['archive']['show_subed_only']))
    set_message('show_subed_only', show_subed_only, expire=False)


def make_folders():
    """ make needed cache folders here so docker doesn't mess it up """
    folders = ['download', 'channels', 'videos', 'import', 'backup']
    config = AppConfig().config
    cache_dir = config['application']['cache_dir']
    for folder in folders:
        folder_path = os.path.join(cache_dir, folder)
        try:
            os.makedirs(folder_path)
        except FileExistsError:
            continue


__all__ = ('celery_app',)
make_folders()
sync_redis_state()
index_check()
