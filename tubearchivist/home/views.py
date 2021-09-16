"""
Functionality:
- all views for home app
- process post data recieved from frontend via ajax
"""

import urllib.parse
import json

from datetime import datetime
from time import sleep

import requests

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views import View
from django.utils.http import urlencode

from home.src.download import PendingList, ChannelSubscription
from home.src.searching import SearchHandler, Pagination
from home.src.config import AppConfig
from home.src.helper import (
    process_url_list,
    get_dl_message,
    get_message,
    set_message
)
from home.tasks import (
    update_subscribed,
    download_pending,
    extrac_dl,
    download_single,
    run_manual_import,
    run_backup
)


class HomeView(View):
    """ resolves to /
    handle home page and video search post functionality
    """

    CONFIG = AppConfig().config
    ES_URL = CONFIG['application']['es_url']

    def get(self, request):
        """ return home search results """
        colors, sort_order, hide_watched = self.read_config()
        # handle search
        search_get = request.GET.get('search', False)
        if search_get:
            search_encoded = urllib.parse.quote(search_get)
        else:
            search_encoded = False
        # define page size
        page_get = int(request.GET.get('page', 0))
        pagination_handler = Pagination(page_get, search_encoded)

        url = self.ES_URL + '/ta_video/_search'

        data = self.build_data(
            pagination_handler, sort_order, search_get, hide_watched
        )

        search = SearchHandler(url, data)
        videos_hits = search.get_data()
        max_hits = search.max_hits
        pagination_handler.validate(max_hits)
        context = {
            'videos': videos_hits,
            'pagination': pagination_handler.pagination,
            'sortorder': sort_order,
            'hide_watched': hide_watched,
            'colors': colors
        }
        return render(request, 'home/home.html', context)

    @staticmethod
    def build_data(pagination_handler, sort_order, search_get, hide_watched):
        """ build the data dict for the search query """
        page_size = pagination_handler.pagination['page_size']
        page_from = pagination_handler.pagination['page_from']
        data = {
            "size": page_size, "from": page_from, "query": {"match_all": {}},
            "sort": [
                {"published": {"order": "desc"}},
                {"date_downloaded": {"order": "desc"}}
            ]
        }
        # define sort
        if sort_order == 'downloaded':
            del data['sort'][0]
        if search_get:
            del data['sort']
        if hide_watched:
            data['query'] = {"term": {"player.watched": {"value": False}}}
        if search_get:
            query = {
                "multi_match": {
                    "query": search_get,
                    "fields": ["title", "channel.channel_name", "tags"],
                    "type": "cross_fields",
                    "operator": "and"
                }
            }
            data['query'] = query

        return data

    @staticmethod
    def read_config():
        """ read needed values from redis """
        config_handler = AppConfig().config
        colors = config_handler['application']['colors']
        sort_order = get_message('sort_order')
        hide_watched = get_message('hide_watched')
        return colors, sort_order, hide_watched

    @staticmethod
    def post(request):
        """ handle post from search form """
        post_data = dict(request.POST)
        search_query = post_data['videoSearch'][0]
        search_url = '/?' + urlencode({'search': search_query})
        return redirect(search_url, permanent=True)


class AboutView(View):
    """ resolves to /about/
    show helpful how to information
    """

    @staticmethod
    def get(request):
        """ handle http get """
        config = AppConfig().config
        colors = config['application']['colors']
        context = {
            'title': 'About',
            'colors': colors
        }
        return render(request, 'home/about.html', context)


class DownloadView(View):
    """ resolves to /download/
    takes POST for downloading youtube links
    """

    @staticmethod
    def get(request):
        """ handle get requests """
        config = AppConfig().config
        colors = config['application']['colors']
        pending_handler = PendingList()
        all_pending, _ = pending_handler.get_all_pending()
        context = {
            'pending': all_pending,
            'title': 'Downloads',
            'colors': colors
        }
        return render(request, 'home/downloads.html', context)

    @staticmethod
    def post(request):
        """ handle post requests """
        download_post = dict(request.POST)
        if 'vid-url' in download_post.keys():
            url_str = download_post['vid-url']
            print('adding to queue')
            youtube_ids = process_url_list(url_str)
            if not youtube_ids:
                # failed to process
                print(url_str)
                mess_dict = {
                    "status": "downloading",
                    "level": "error",
                    "title": 'Failed to extract links.',
                    "message": ''
                }
                set_message('progress:download', mess_dict)
                return redirect('downloads')

            print(youtube_ids)
            extrac_dl.delay(youtube_ids)

        sleep(2)
        return redirect('downloads', permanent=True)


class ChannelIdView(View):
    """ resolves to /chanel/<channel-id>/
    display single channel page from channel_id
    """

    def get(self, request, channel_id_detail):
        """ get method """
        es_url, colors = self.read_config()
        context = self.get_channel_videos(request, channel_id_detail, es_url)
        context.update({'colors': colors})
        return render(request, 'home/channel_id.html', context)

    @staticmethod
    def read_config():
        """ read config file """
        config = AppConfig().config
        es_url = config['application']['es_url']
        colors = config['application']['colors']
        return es_url, colors

    def get_channel_videos(self, request, channel_id_detail, es_url):
        """ get channel from video index """
        page_get = int(request.GET.get('page', 0))
        pagination_handler = Pagination(page_get)
        # get data
        url = es_url + '/ta_video/_search'
        data = self.build_data(pagination_handler, channel_id_detail)
        search = SearchHandler(url, data)
        videos_hits = search.get_data()
        max_hits = search.max_hits
        if max_hits:
            channel_info = videos_hits[0]['source']['channel']
            channel_name = channel_info['channel_name']
            pagination_handler.validate(max_hits)
            pagination = pagination_handler.pagination
        else:
            # get details from channel index when when no hits
            channel_info, channel_name = self.get_channel_info(
                channel_id_detail, es_url
            )
            videos_hits = False
            pagination = False

        context = {
            'channel_info': channel_info,
            'videos': videos_hits,
            'max_hits': max_hits,
            'pagination': pagination,
            'title': 'Channel: ' + channel_name,
        }

        return context

    @staticmethod
    def build_data(pagination_handler, channel_id_detail):
        """ build data dict for search """
        page_size = pagination_handler.pagination['page_size']
        page_from = pagination_handler.pagination['page_from']
        data = {
            "size": page_size, "from": page_from,
            "query": {
                "term": {"channel.channel_id": {"value": channel_id_detail}}
            },
            "sort": [
                {"published": {"order": "desc"}},
                {"date_downloaded": {"order": "desc"}}
            ]
        }
        return data

    @staticmethod
    def get_channel_info(channel_id_detail, es_url):
        """ get channel info from channel index if no videos """
        url = f'{es_url}/ta_channel/_doc/{channel_id_detail}'
        data = False
        search = SearchHandler(url, data)
        channel_data = search.get_data()
        channel_info = channel_data[0]['source']
        channel_name = channel_info['channel_name']
        return channel_info, channel_name


class ChannelView(View):
    """ resolves to /channel/
    handle functionality for channel overview page, subscribe to channel,
    search as you type for channel name
    """

    def get(self, request):
        """ handle http get requests """
        es_url, colors = self.read_config()
        page_get = int(request.GET.get('page', 0))
        pagination_handler = Pagination(page_get)
        page_size = pagination_handler.pagination['page_size']
        page_from = pagination_handler.pagination['page_from']
        # get
        url = es_url + '/ta_channel/_search'
        data = {
            "size": page_size, "from": page_from, "query": {"match_all": {}},
            "sort": [{"channel_name.keyword": {"order": "asc"}}]
        }
        show_subed_only = get_message('show_subed_only')
        if show_subed_only:
            data['query'] = {"term": {"channel_subscribed": {"value": True}}}
        search = SearchHandler(url, data)
        channel_hits = search.get_data()
        max_hits = search.max_hits
        pagination_handler.validate(search.max_hits)
        context = {
            'channels': channel_hits,
            'max_hits': max_hits,
            'pagination': pagination_handler.pagination,
            'show_subed_only': show_subed_only,
            'title': 'Channels',
            'colors': colors
        }
        return render(request, 'home/channel.html', context)

    @staticmethod
    def read_config():
        """ read config file """
        config = AppConfig().config
        es_url = config['application']['es_url']
        colors = config['application']['colors']
        return es_url, colors

    def post(self, request):
        """ handle http post requests """
        subscriptions_post = dict(request.POST)
        print(subscriptions_post)
        subscriptions_post = dict(request.POST)
        if 'subscribe' in subscriptions_post.keys():
            sub_str = subscriptions_post['subscribe']
            try:
                youtube_ids = process_url_list(sub_str)
                self.subscribe_to(youtube_ids)
            except ValueError:
                print('parsing subscribe ids failed!')
                print(sub_str)

        sleep(1)
        return redirect('channel', permanent=True)

    @staticmethod
    def subscribe_to(youtube_ids):
        """ process the subscribe ids """
        for youtube_id in youtube_ids:
            if youtube_id['type'] == 'video':
                to_sub = youtube_id['url']
                vid_details = PendingList().get_youtube_details(to_sub)
                channel_id_sub = vid_details['channel_id']
            elif youtube_id['type'] == 'channel':
                channel_id_sub = youtube_id['url']
            else:
                raise ValueError('failed to subscribe to: ' + youtube_id)

            ChannelSubscription().change_subscribe(
                channel_id_sub, channel_subscribed=True
            )
            print('subscribed to: ' + channel_id_sub)


class VideoView(View):
    """ resolves to /video/<video-id>/
    display details about a single video
    """

    def get(self, request, video_id):
        """ get single video """
        es_url, colors = self.read_config()
        url = f'{es_url}/ta_video/_doc/{video_id}'
        data = None
        look_up = SearchHandler(url, data)
        video_hit = look_up.get_data()
        video_data = video_hit[0]['source']
        video_title = video_data['title']
        context = {
            'video': video_data,
            'title': video_title,
            'colors': colors
        }
        return render(request, 'home/video.html', context)

    @staticmethod
    def read_config():
        """ read config file """
        config = AppConfig().config
        es_url = config['application']['es_url']
        colors = config['application']['colors']
        return es_url, colors


class SettingsView(View):
    """ resolves to /settings/
    handle the settings page, display current settings,
    take post request from the form to update settings
    """

    @staticmethod
    def get(request):
        """ read and display current settings """
        config = AppConfig().config
        colors = config['application']['colors']

        context = {
            'title': 'Settings',
            'config': config,
            'colors': colors
        }

        return render(request, 'home/settings.html', context)

    @staticmethod
    def post(request):
        """ handle form post to update settings """
        form_post = dict(request.POST)
        del form_post['csrfmiddlewaretoken']
        print(form_post)
        config_handler = AppConfig()
        config_handler.update_config(form_post)

        return redirect('settings', permanent=True)


def progress(request):
    # pylint: disable=unused-argument
    """ endpoint for download progress ajax calls """
    config = AppConfig().config
    cache_dir = config['application']['cache_dir']
    json_data = get_dl_message(cache_dir)
    return JsonResponse(json_data)


def process(request):
    """ handle all the buttons calls via POST ajax """
    if request.method == 'POST':
        post_dict = json.loads(request.body.decode())
        post_handler = PostData(post_dict)
        if post_handler.to_do:
            task_result = post_handler.run_task()
            return JsonResponse(task_result)

    return JsonResponse({'success': False})


class PostData:
    """ generic post handler from process route """

    CONFIG = AppConfig().config
    ES_URL = CONFIG['application']['es_url']

    VALID_KEYS = [
        "watched", "rescan_pending", "ignore", "dl_pending",
        "unsubscribe", "sort_order", "hide_watched", "show_subed_only",
        "channel-search", "video-search", "dlnow", "manual-import",
        "db-backup"
    ]

    def __init__(self, post_dict):
        self.post_dict = post_dict
        self.to_do = self.validate()

    def validate(self):
        """ validate the post_dict """
        to_do = []
        for key, value in self.post_dict.items():
            if key in self.VALID_KEYS:
                task_item = {'task': key, 'status': value}
                print(task_item)
                to_do.append(task_item)
            else:
                print(key + ' not a valid key')

        return to_do

    def run_task(self):
        """ run through the tasks to do """
        for item in self.to_do:
            task = item['task']
            if task == 'watched':
                youtube_id = item['status']
                self.parse_watched(youtube_id)
            elif task == 'rescan_pending':
                print('rescan subscribed channels')
                update_subscribed.delay()
            elif task == 'ignore':
                print('ignore video')
                handler = PendingList()
                ignore_list = item['status']
                handler.ignore_from_pending([ignore_list])
            elif task == 'dl_pending':
                print('download pending')
                download_pending.delay()
            elif task == 'unsubscribe':
                channel_id_unsub = item['status']
                print('unsubscribe from ' + channel_id_unsub)
                ChannelSubscription().change_subscribe(
                    channel_id_unsub, channel_subscribed=False
                )
            elif task == 'sort_order':
                sort_order = item['status']
                set_message('sort_order', sort_order, expire=False)
            elif task == 'hide_watched':
                hide_watched = bool(int(item['status']))
                print(item['status'])
                set_message('hide_watched', hide_watched, expire=False)
            elif task == 'show_subed_only':
                show_subed_only = bool(int(item['status']))
                print(show_subed_only)
                set_message('show_subed_only', show_subed_only, expire=False)
            elif task == 'channel-search':
                search_query = item['status']
                print('searching for: ' + search_query)
                search_results = self.search_channels(search_query)
                return search_results
            elif task == 'video-search':
                search_query = item['status']
                print('searching for: ' + search_query)
                search_results = self.search_videos(search_query)
                return search_results
            elif task == 'dlnow':
                youtube_id = item['status']
                print('downloading: ' + youtube_id)
                download_single(youtube_id)
            elif task == 'manual-import':
                print('starting manual import')
                run_manual_import.delay()
            elif task == 'db-backup':
                print('backing up database')
                run_backup.delay()
        return {'success': True}

    def search_channels(self, search_query):
        """ fancy searching channels as you type """
        url = self.ES_URL + '/ta_channel/_search'
        data = {
            "size": 10,
            "query": {
                "multi_match": {
                    "query": search_query,
                    "type": "bool_prefix",
                    "fields": [
                        "channel_name.search_as_you_type",
                        "channel_name._2gram",
                        "channel_name._3gram"
                    ]
                }
            }
        }
        look_up = SearchHandler(url, data, cache=False)
        search_results = look_up.get_data()
        return {'results': search_results}

    def search_videos(self, search_query):
        """ fancy searching videos as you type """
        url = self.ES_URL + '/ta_video/_search'
        data = {
            "size": 10,
            "query": {
                "multi_match": {
                    "query": search_query,
                    "type": "bool_prefix",
                    "fields": [
                        "title.search_as_you_type",
                        "title._2gram",
                        "title._3gram"
                    ]
                }
            }
        }
        look_up = SearchHandler(url, data, cache=False)
        search_results = look_up.get_data()
        return {'results': search_results}

    def parse_watched(self, youtube_id):
        """ marked as watched based on id type """
        es_url = self.ES_URL
        id_type = process_url_list([youtube_id])[0]['type']
        stamp = int(datetime.now().strftime("%s"))
        if id_type == 'video':
            stamp = int(datetime.now().strftime("%s"))
            url = self.ES_URL + '/ta_video/_update/' + youtube_id
            source = {
                "doc": {"player": {"watched": True, "watched_date": stamp}}
            }
            request = requests.post(url, json=source)
            if not request.ok:
                print(request.text)
        elif id_type == 'channel':
            headers = {'Content-type': 'application/json'}
            data = {
                "description": youtube_id,
                "processors": [
                    {"set": {"field": "player.watched", "value": True}},
                    {"set": {"field": "player.watched_date", "value": stamp}}
                ]
            }
            payload = json.dumps(data)
            url = es_url + '/_ingest/pipeline/' + youtube_id
            request = requests.put(url, data=payload, headers=headers)
            if not request.ok:
                print(request.text)
            # apply pipeline
            must_list = [
                {"term": {"channel.channel_id": {"value": youtube_id}}},
                {"term": {"player.watched": {"value": False}}}
            ]
            data = {"query": {"bool": {"must": must_list}}}
            payload = json.dumps(data)
            url = f'{es_url}/ta_video/_update_by_query?pipeline={youtube_id}'
            request = requests.post(url, data=payload, headers=headers)
            if not request.ok:
                print(request.text)
