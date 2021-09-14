"""
Functionality:
- handle search to populate results to view
- cache youtube video thumbnails and channel artwork
- parse values in hit_cleanup for frontend
- calculate pagination values
"""

import math
import os
import urllib.parse

from datetime import datetime

import requests

from PIL import Image

from home.src.config import AppConfig


class SearchHandler:
    """ search elastic search """

    CONFIG = AppConfig().config
    CACHE_DIR = CONFIG['application']['cache_dir']

    def __init__(self, url, data, cache=True):
        self.max_hits = None
        self.url = url
        self.data = data
        self.cache = cache

    def get_data(self):
        """ get the data """
        if self.data:
            response = requests.get(self.url, json=self.data).json()
        else:
            response = requests.get(self.url).json()

        if 'hits' in response.keys():
            self.max_hits = response['hits']['total']['value']
            return_value = response['hits']['hits']
        else:
            # simulate list for single result to reuse rest of class
            return_value = [response]

        # stop if empty
        if not return_value:
            return False

        all_videos = []
        all_channels = []
        for idx, hit in enumerate(return_value):
            return_value[idx] = self.hit_cleanup(hit)
            if hit['_index'] == 'ta_video':
                video_dict, channel_dict = self.vid_cache_link(hit)
                if video_dict not in all_videos:
                    all_videos.append(video_dict)
                if channel_dict not in all_channels:
                    all_channels.append(channel_dict)
            elif hit['_index'] == 'ta_channel':
                channel_dict = self.channel_cache_link(hit)
                if channel_dict not in all_channels:
                    all_channels.append(channel_dict)
        if self.cache:
            # validate cache
            self.cache_dl_vids(all_videos)
            self.cache_dl_chan(all_channels)

        return return_value

    @staticmethod
    def vid_cache_link(hit):
        """ download thumbnails into chache """
        vid_thumb = hit['source']['vid_thumb_url']
        youtube_id = hit['source']['youtube_id']
        channel_id_hit = hit['source']['channel']['channel_id']
        chan_thumb = hit['source']['channel']['channel_thumb_url']
        try:
            chan_banner = hit['source']['channel']['channel_banner_url']
        except KeyError:
            chan_banner = False
        video_dict = {
            'youtube_id': youtube_id,
            'vid_thumb': vid_thumb
        }
        channel_dict = {
            'channel_id': channel_id_hit,
            'chan_thumb': chan_thumb,
            'chan_banner': chan_banner
        }
        return video_dict, channel_dict

    @staticmethod
    def channel_cache_link(hit):
        """ build channel thumb links """
        channel_id_hit = hit['source']['channel_id']
        chan_thumb = hit['source']['channel_thumb_url']
        try:
            chan_banner = hit['source']['channel_banner_url']
        except KeyError:
            chan_banner = False
        channel_dict = {
            'channel_id': channel_id_hit,
            'chan_thumb': chan_thumb,
            'chan_banner': chan_banner
        }
        return channel_dict

    def cache_dl_vids(self, all_videos):
        """ video thumbs links for cache """
        vid_cache = os.path.join(self.CACHE_DIR, 'videos')
        all_vid_cached = os.listdir(vid_cache)
        # videos
        for video_dict in all_videos:
            youtube_id = video_dict['youtube_id']
            if not youtube_id + '.jpg' in all_vid_cached:
                cache_path = os.path.join(vid_cache, youtube_id + '.jpg')
                thumb_url = video_dict['vid_thumb']
                img_raw = requests.get(thumb_url, stream=True).raw
                img = Image.open(img_raw)
                width, height = img.size
                if not width / height == 16 / 9:
                    new_height = width / 16 * 9
                    offset = (height - new_height) / 2
                    img = img.crop((0, offset, width, height - offset))
                img.convert("RGB").save(cache_path)

    def cache_dl_chan(self, all_channels):
        """ download channel thumbs """
        chan_cache = os.path.join(self.CACHE_DIR, 'channels')
        all_chan_cached = os.listdir(chan_cache)
        for channel_dict in all_channels:
            channel_id_cache = channel_dict['channel_id']
            channel_banner_url = channel_dict['chan_banner']
            channel_banner = channel_id_cache + '_banner.jpg'
            channel_thumb_url = channel_dict['chan_thumb']
            channel_thumb = channel_id_cache + '_thumb.jpg'
            # thumb
            if channel_thumb_url and channel_thumb not in all_chan_cached:
                cache_path = os.path.join(chan_cache, channel_thumb)
                img_raw = requests.get(channel_thumb_url, stream=True).content
                with open(cache_path, 'wb') as f:
                    f.write(img_raw)
            # banner
            if channel_banner_url and channel_banner not in all_chan_cached:
                cache_path = os.path.join(chan_cache, channel_banner)
                img_raw = requests.get(channel_banner_url, stream=True).content
                with open(cache_path, 'wb') as f:
                    f.write(img_raw)

    @staticmethod
    def hit_cleanup(hit):
        """ clean up and parse data from a single hit """
        hit['source'] = hit.pop('_source')
        hit_keys = hit['source'].keys()
        if 'media_url' in hit_keys:
            parsed_url = urllib.parse.quote(hit['source']['media_url'])
            hit['source']['media_url'] = parsed_url

        if 'published' in hit_keys:
            published = hit['source']['published']
            date_pub = datetime.strptime(published, "%Y-%m-%d")
            date_str = datetime.strftime(date_pub, "%d %b, %Y")
            hit['source']['published'] = date_str

        if 'vid_last_refresh' in hit_keys:
            vid_last_refresh = hit['source']['vid_last_refresh']
            date_refresh = datetime.fromtimestamp(vid_last_refresh)
            date_str = datetime.strftime(date_refresh, "%d %b, %Y")
            hit['source']['vid_last_refresh'] = date_str

        if 'channel_last_refresh' in hit_keys:
            refreshed = hit['source']['channel_last_refresh']
            date_refresh = datetime.fromtimestamp(refreshed)
            date_str = datetime.strftime(date_refresh, "%d %b, %Y")
            hit['source']['channel_last_refresh'] = date_str

        if 'channel' in hit_keys:
            channel_keys = hit['source']['channel'].keys()
            if 'channel_last_refresh' in channel_keys:
                refreshed = hit['source']['channel']['channel_last_refresh']
                date_refresh = datetime.fromtimestamp(refreshed)
                date_str = datetime.strftime(date_refresh, "%d %b, %Y")
                hit['source']['channel']['channel_last_refresh'] = date_str

        return hit


class Pagination:
    """
    figure out the pagination based on page size and total_hits
    """

    def __init__(self, page_get, search_get=False):
        config = AppConfig().config
        self.page_size = config['archive']['page_size']
        self.page_get = page_get
        self.search_get = search_get
        self.pagination = self.first_guess()

    def first_guess(self):
        """ build first guess before api call """
        page_get = self.page_get
        if page_get in [0, 1]:
            page_from = 0
            prev_pages = False
        elif page_get > 1:
            page_from = (page_get - 1) * self.page_size
            prev_pages = [
                i for i in range(page_get - 1, page_get - 6, -1) if i > 1
            ]
            prev_pages.reverse()
        pagination = {
            "page_size": self.page_size,
            "page_from": page_from,
            "prev_pages": prev_pages,
            "current_page": page_get
        }
        if self.search_get:
            pagination.update({"search_get": self.search_get})
        return pagination

    def validate(self, total_hits):
        """ validate pagination with total_hits after making api call """
        page_get = self.page_get
        max_pages = math.ceil(total_hits / self.page_size)
        if page_get < max_pages and max_pages > 1:
            self.pagination['last_page'] = max_pages
        else:
            self.pagination['last_page'] = False
        next_pages = [
            i for i in range(page_get + 1, page_get + 6) if 1 < i < max_pages
        ]

        self.pagination['next_pages'] = next_pages
