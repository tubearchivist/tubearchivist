"""
Functionality:
- all views for home app
- process post data received from frontend via ajax
"""

import json
import urllib.parse
from time import sleep

from django import forms
from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils.http import urlencode
from django.views import View
from home.forms import (
    AddToQueueForm,
    ApplicationSettingsForm,
    ChannelSearchForm,
    CustomAuthForm,
    PlaylistSearchForm,
    SubscribeToChannelForm,
    SubscribeToPlaylistForm,
    UserSettingsForm,
    VideoSearchForm,
)
from home.src.config import AppConfig
from home.src.frontend import PostData
from home.src.helper import RedisArchivist, UrlListParser
from home.src.index import YoutubePlaylist
from home.src.searching import Pagination, SearchHandler
from home.tasks import extrac_dl, subscribe_to


class HomeView(View):
    """resolves to /
    handle home page and video search post functionality
    """

    CONFIG = AppConfig().config
    ES_URL = CONFIG["application"]["es_url"]

    def get(self, request):
        """return home search results"""
        user_id = request.user.id
        view_config = self.read_config(user_id)
        # handle search
        search_get = request.GET.get("search", False)
        if search_get:
            search_encoded = urllib.parse.quote(search_get)
        else:
            search_encoded = False
        # define page size
        page_get = int(request.GET.get("page", 0))
        pagination_handler = Pagination(
            page_get, user_id, search_get=search_encoded
        )

        url = self.ES_URL + "/ta_video/_search"
        data = self.build_data(
            pagination_handler,
            view_config["sort_by"],
            view_config["sort_order"],
            search_get,
            view_config["hide_watched"],
        )

        search = SearchHandler(url, data)
        videos_hits = search.get_data()
        max_hits = search.max_hits
        pagination_handler.validate(max_hits)

        search_form = VideoSearchForm()
        context = {
            "search_form": search_form,
            "videos": videos_hits,
            "pagination": pagination_handler.pagination,
            "sort_by": view_config["sort_by"],
            "sort_order": view_config["sort_order"],
            "hide_watched": view_config["hide_watched"],
            "colors": view_config["colors"],
            "view_style": view_config["view_style"],
        }
        return render(request, "home/home.html", context)

    @staticmethod
    def build_data(
        pagination_handler, sort_by, sort_order, search_get, hide_watched
    ):
        """build the data dict for the search query"""
        page_size = pagination_handler.pagination["page_size"]
        page_from = pagination_handler.pagination["page_from"]

        # overwrite sort_by to match key
        if sort_by == "views":
            sort_by = "stats.view_count"
        elif sort_by == "likes":
            sort_by = "stats.like_count"
        elif sort_by == "downloaded":
            sort_by = "date_downloaded"

        data = {
            "size": page_size,
            "from": page_from,
            "query": {"match_all": {}},
            "sort": [{sort_by: {"order": sort_order}}],
        }
        if hide_watched:
            data["query"] = {"term": {"player.watched": {"value": False}}}
        if search_get:
            del data["sort"]
            query = {
                "multi_match": {
                    "query": search_get,
                    "fields": ["title", "channel.channel_name", "tags"],
                    "type": "cross_fields",
                    "operator": "and",
                }
            }
            data["query"] = query

        return data

    @staticmethod
    def read_config(user_id):
        """read needed values from redis"""
        config_handler = AppConfig(user_id)

        view_key = f"{user_id}:view:home"
        view_style = RedisArchivist().get_message(view_key)["status"]
        if not view_style:
            view_style = config_handler.config["default_view"]["home"]

        sort_by = RedisArchivist().get_message(f"{user_id}:sort_by")["status"]
        if not sort_by:
            sort_by = config_handler.config["archive"]["sort_by"]

        sort_order_key = f"{user_id}:sort_order"
        sort_order = RedisArchivist().get_message(sort_order_key)["status"]
        if not sort_order:
            sort_order = config_handler.config["archive"]["sort_order"]

        hide_watched_key = f"{user_id}:hide_watched"
        hide_watched = RedisArchivist().get_message(hide_watched_key)["status"]
        view_config = {
            "colors": config_handler.colors,
            "view_style": view_style,
            "sort_by": sort_by,
            "sort_order": sort_order,
            "hide_watched": hide_watched,
        }
        return view_config

    @staticmethod
    def post(request):
        """handle post from search form"""
        search_form = VideoSearchForm(data=request.POST)
        if search_form.is_valid():
            search_query = request.POST.get("searchInput")
            print(search_query)
            search_url = "/?" + urlencode({"search": search_query})
            return redirect(search_url, permanent=True)

        return redirect("home")


class LoginView(View):
    """resolves to /login/
    Greeting and login page
    """

    @staticmethod
    def get(request):
        """handle get requests"""
        failed = bool(request.GET.get("failed"))
        colors = AppConfig(request.user.id).colors
        form = CustomAuthForm()
        context = {"colors": colors, "form": form, "form_error": failed}
        return render(request, "home/login.html", context)

    @staticmethod
    def post(request):
        """handle login post request"""
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            next_url = request.POST.get("next") or "home"
            user = form.get_user()
            login(request, user)
            return redirect(next_url)

        return redirect("/login?failed=true")


class AboutView(View):
    """resolves to /about/
    show helpful how to information
    """

    @staticmethod
    def get(request):
        """handle http get"""
        colors = AppConfig(request.user.id).colors
        context = {"title": "About", "colors": colors}
        return render(request, "home/about.html", context)


class DownloadView(View):
    """resolves to /download/
    takes POST for downloading youtube links
    """

    def get(self, request):
        """handle get requests"""
        user_id = request.user.id
        view_config = self.read_config(user_id)

        page_get = int(request.GET.get("page", 0))
        pagination_handler = Pagination(page_get, user_id)

        url = view_config["es_url"] + "/ta_download/_search"
        data = self.build_data(
            pagination_handler, view_config["show_ignored_only"]
        )
        search = SearchHandler(url, data)

        videos_hits = search.get_data()
        max_hits = search.max_hits

        if videos_hits:
            all_video_hits = [i["source"] for i in videos_hits]
            pagination_handler.validate(max_hits)
            pagination = pagination_handler.pagination
        else:
            all_video_hits = False
            pagination = False

        add_form = AddToQueueForm()
        context = {
            "add_form": add_form,
            "all_video_hits": all_video_hits,
            "max_hits": max_hits,
            "pagination": pagination,
            "title": "Downloads",
            "colors": view_config["colors"],
            "show_ignored_only": view_config["show_ignored_only"],
            "view_style": view_config["view_style"],
        }
        return render(request, "home/downloads.html", context)

    @staticmethod
    def read_config(user_id):
        """read config vars"""
        config_handler = AppConfig(user_id)
        view_key = f"{user_id}:view:downloads"
        view_style = RedisArchivist().get_message(view_key)["status"]
        if not view_style:
            view_style = config_handler.config["default_view"]["downloads"]

        ignored = RedisArchivist().get_message(f"{user_id}:show_ignored_only")
        show_ignored_only = ignored["status"]

        es_url = config_handler.config["application"]["es_url"]

        view_config = {
            "es_url": es_url,
            "colors": config_handler.colors,
            "view_style": view_style,
            "show_ignored_only": show_ignored_only,
        }
        return view_config

    @staticmethod
    def build_data(pagination_handler, show_ignored_only):
        """build data dict for search"""
        page_size = pagination_handler.pagination["page_size"]
        page_from = pagination_handler.pagination["page_from"]
        if show_ignored_only:
            filter_view = "ignore"
        else:
            filter_view = "pending"

        data = {
            "size": page_size,
            "from": page_from,
            "query": {"term": {"status": {"value": filter_view}}},
            "sort": [{"timestamp": {"order": "asc"}}],
        }
        return data

    @staticmethod
    def post(request):
        """handle post requests"""
        to_queue = AddToQueueForm(data=request.POST)
        if to_queue.is_valid():
            url_str = request.POST.get("vid_url")
            print(url_str)
            try:
                youtube_ids = UrlListParser(url_str).process_list()
            except ValueError:
                # failed to process
                print(f"failed to parse: {url_str}")
                mess_dict = {
                    "status": "downloading",
                    "level": "error",
                    "title": "Failed to extract links.",
                    "message": "Not a video, channel or playlist ID or URL",
                }
                RedisArchivist().set_message("progress:download", mess_dict)
                return redirect("downloads")

            print(youtube_ids)
            extrac_dl.delay(youtube_ids)

        sleep(2)
        return redirect("downloads", permanent=True)


class ChannelIdView(View):
    """resolves to /channel/<channel-id>/
    display single channel page from channel_id
    """

    def get(self, request, channel_id_detail):
        """get method"""
        # es_url, colors, view_style = self.read_config()
        view_config = self.read_config(user_id=request.user.id)
        context = self.get_channel_videos(
            request, channel_id_detail, view_config
        )
        context.update(view_config)
        return render(request, "home/channel_id.html", context)

    @staticmethod
    def read_config(user_id):
        """read config file"""
        config_handler = AppConfig(user_id)
        config = config_handler.config

        view_key = f"{user_id}:view:home"
        view_style = RedisArchivist().get_message(view_key)["status"]
        if not view_style:
            view_style = config_handler.config["default_view"]["home"]

        sort_by = RedisArchivist().get_message(f"{user_id}:sort_by")["status"]
        if not sort_by:
            sort_by = config["archive"]["sort_by"]

        sort_order_key = f"{user_id}:sort_order"
        sort_order = RedisArchivist().get_message(sort_order_key)["status"]
        if not sort_order:
            sort_order = config["archive"]["sort_order"]

        hide_watched_key = f"{user_id}:hide_watched"
        hide_watched = RedisArchivist().get_message(hide_watched_key)["status"]

        view_config = {
            "colors": config_handler.colors,
            "es_url": config["application"]["es_url"],
            "view_style": view_style,
            "sort_by": sort_by,
            "sort_order": sort_order,
            "hide_watched": hide_watched,
        }
        return view_config

    def get_channel_videos(self, request, channel_id_detail, view_config):
        """get channel from video index"""
        page_get = int(request.GET.get("page", 0))
        pagination_handler = Pagination(page_get, request.user.id)
        # get data
        url = view_config["es_url"] + "/ta_video/_search"
        data = self.build_data(
            pagination_handler, channel_id_detail, view_config
        )
        search = SearchHandler(url, data)
        videos_hits = search.get_data()
        max_hits = search.max_hits
        if max_hits:
            channel_info = videos_hits[0]["source"]["channel"]
            channel_name = channel_info["channel_name"]
            pagination_handler.validate(max_hits)
            pagination = pagination_handler.pagination
        else:
            # get details from channel index when when no hits
            channel_info, channel_name = self.get_channel_info(
                channel_id_detail, view_config["es_url"]
            )
            videos_hits = False
            pagination = False

        context = {
            "channel_info": channel_info,
            "videos": videos_hits,
            "max_hits": max_hits,
            "pagination": pagination,
            "title": "Channel: " + channel_name,
        }

        return context

    @staticmethod
    def build_data(pagination_handler, channel_id_detail, view_config):
        """build data dict for search"""
        sort_by = view_config["sort_by"]
        sort_order = view_config["sort_order"]

        # overwrite sort_by to match key
        if sort_by == "views":
            sort_by = "stats.view_count"
        elif sort_by == "likes":
            sort_by = "stats.like_count"
        elif sort_by == "downloaded":
            sort_by = "date_downloaded"

        data = {
            "size": pagination_handler.pagination["page_size"],
            "from": pagination_handler.pagination["page_from"],
            "query": {
                "bool": {
                    "must": [
                        {
                            "term": {
                                "channel.channel_id": {
                                    "value": channel_id_detail
                                }
                            }
                        }
                    ]
                }
            },
            "sort": [{sort_by: {"order": sort_order}}],
        }
        if view_config["hide_watched"]:
            to_append = {"term": {"player.watched": {"value": False}}}
            data["query"]["bool"]["must"].append(to_append)

        return data

    @staticmethod
    def get_channel_info(channel_id_detail, es_url):
        """get channel info from channel index if no videos"""
        url = f"{es_url}/ta_channel/_doc/{channel_id_detail}"
        data = False
        search = SearchHandler(url, data)
        channel_data = search.get_data()
        channel_info = channel_data[0]["source"]
        channel_name = channel_info["channel_name"]
        return channel_info, channel_name


class ChannelView(View):
    """resolves to /channel/
    handle functionality for channel overview page, subscribe to channel,
    search as you type for channel name
    """

    def get(self, request):
        """handle http get requests"""
        user_id = request.user.id
        view_config = self.read_config(user_id=user_id)
        page_get = int(request.GET.get("page", 0))
        pagination_handler = Pagination(page_get, user_id)

        # get
        url = view_config["es_url"] + "/ta_channel/_search"
        data = {
            "size": pagination_handler.pagination["page_size"],
            "from": pagination_handler.pagination["page_from"],
            "query": {"match_all": {}},
            "sort": [{"channel_name.keyword": {"order": "asc"}}],
        }
        if view_config["show_subed_only"]:
            data["query"] = {"term": {"channel_subscribed": {"value": True}}}
        search = SearchHandler(url, data)
        channel_hits = search.get_data()
        pagination_handler.validate(search.max_hits)
        search_form = ChannelSearchForm()
        subscribe_form = SubscribeToChannelForm()
        context = {
            "search_form": search_form,
            "subscribe_form": subscribe_form,
            "channels": channel_hits,
            "max_hits": search.max_hits,
            "pagination": pagination_handler.pagination,
            "show_subed_only": view_config["show_subed_only"],
            "title": "Channels",
            "colors": view_config["colors"],
            "view_style": view_config["view_style"],
            "running": view_config["running"],
        }
        return render(request, "home/channel.html", context)

    @staticmethod
    def read_config(user_id):
        """read config file"""
        config_handler = AppConfig(user_id)
        view_key = f"{user_id}:view:channel"
        view_style = RedisArchivist().get_message(view_key)["status"]
        running = RedisArchivist().get_message("progress:subscribe")["status"]
        if not view_style:
            view_style = config_handler.config["default_view"]["channel"]

        sub_only_key = f"{user_id}:show_subed_only"
        show_subed_only = RedisArchivist().get_message(sub_only_key)["status"]

        view_config = {
            "es_url": config_handler.config["application"]["es_url"],
            "view_style": view_style,
            "show_subed_only": show_subed_only,
            "colors": config_handler.colors,
            "running": running,
        }

        return view_config

    @staticmethod
    def post(request):
        """handle http post requests"""
        subscribe_form = SubscribeToChannelForm(data=request.POST)
        if subscribe_form.is_valid():
            RedisArchivist().set_message(
                "progress:subscribe", {"status": "subscribing"}
            )
            url_str = request.POST.get("subscribe")
            print(url_str)
            subscribe_to.delay(url_str)

        sleep(1)
        return redirect("channel", permanent=True)


class PlaylistIdView(View):
    """resolves to /playlist/<playlist_id>
    show all videos in a playlist
    """

    def get(self, request, playlist_id_detail):
        """handle get request"""
        view_config = self.read_config(user_id=request.user.id)
        context = self.get_playlist_videos(
            request, playlist_id_detail, view_config
        )
        context.update(view_config)
        return render(request, "home/playlist_id.html", context)

    @staticmethod
    def read_config(user_id):
        """build config dict"""
        config_handler = AppConfig(user_id)
        config = config_handler.config

        view_key = f"{user_id}:view:home"
        view_style = RedisArchivist().get_message(view_key)["status"]
        if not view_style:
            view_style = config_handler.config["default_view"]["home"]

        sort_by = RedisArchivist().get_message(f"{user_id}:sort_by")["status"]
        if not sort_by:
            sort_by = config["archive"]["sort_by"]

        sort_order_key = f"{user_id}:sort_order"
        sort_order = RedisArchivist().get_message(sort_order_key)["status"]
        if not sort_order:
            sort_order = config["archive"]["sort_order"]

        hide_watched_key = f"{user_id}:hide_watched"
        hide_watched = RedisArchivist().get_message(hide_watched_key)["status"]

        view_config = {
            "colors": config_handler.colors,
            "es_url": config["application"]["es_url"],
            "view_style": view_style,
            "sort_by": sort_by,
            "sort_order": sort_order,
            "hide_watched": hide_watched,
        }
        return view_config

    def get_playlist_videos(self, request, playlist_id_detail, view_config):
        """get matching videos for playlist"""
        page_get = int(request.GET.get("page", 0))
        pagination_handler = Pagination(page_get, request.user.id)
        # get data
        playlist_info = self.get_playlist_info(
            playlist_id_detail, view_config["es_url"]
        )
        sort = {
            i["youtube_id"]: i["idx"]
            for i in playlist_info["playlist_entries"]
        }
        playlist_name = playlist_info["playlist_name"]
        data = self.build_data(
            pagination_handler, playlist_id_detail, view_config, sort
        )
        search = SearchHandler(
            view_config["es_url"] + "/ta_video/_search", data
        )
        videos_hits = search.get_data()
        channel_info = self.get_channel_info(
            playlist_info["playlist_channel_id"], view_config["es_url"]
        )

        if search.max_hits:
            pagination_handler.validate(search.max_hits)
            pagination = pagination_handler.pagination
        else:
            videos_hits = False
            pagination = False

        context = {
            "playlist_info": playlist_info,
            "playlist_name": playlist_name,
            "channel_info": channel_info,
            "videos": videos_hits,
            "max_hits": search.max_hits,
            "pagination": pagination,
            "title": "Playlist: " + playlist_name,
        }

        return context

    @staticmethod
    def build_data(pagination_handler, playlist_id_detail, view_config, sort):
        """build data query for es"""
        sort_by = view_config["sort_by"]

        # overwrite sort_by to match key
        if sort_by == "views":
            sort_by = "stats.view_count"
        elif sort_by == "likes":
            sort_by = "stats.like_count"
        elif sort_by == "downloaded":
            sort_by = "date_downloaded"

        script = (
            "if(params.scores.containsKey(doc['youtube_id'].value)) "
            + "{return params.scores[doc['youtube_id'].value];} "
            + "return 100000;"
        )

        data = {
            "size": pagination_handler.pagination["page_size"],
            "from": pagination_handler.pagination["page_from"],
            "query": {
                "bool": {
                    "must": [
                        {"match": {"playlist.keyword": playlist_id_detail}}
                    ]
                }
            },
            "sort": [
                {
                    "_script": {
                        "type": "number",
                        "script": {
                            "lang": "painless",
                            "source": script,
                            "params": {"scores": sort},
                        },
                        "order": "asc",
                    }
                }
            ],
        }
        if view_config["hide_watched"]:
            to_append = {"term": {"player.watched": {"value": False}}}
            data["query"]["bool"]["must"].append(to_append)

        return data

    @staticmethod
    def get_channel_info(channel_id_detail, es_url):
        """get channel info from channel index if no videos"""
        url = f"{es_url}/ta_channel/_doc/{channel_id_detail}"
        search = SearchHandler(url, data=False)
        channel_data = search.get_data()
        channel_info = channel_data[0]["source"]
        return channel_info

    @staticmethod
    def get_playlist_info(playlist_id_detail, es_url):
        """get playlist info header to no fail if playlist is empty"""
        url = f"{es_url}/ta_playlist/_doc/{playlist_id_detail}"
        search = SearchHandler(url, data=False)
        playlist_data = search.get_data()
        playlist_info = playlist_data[0]["source"]
        return playlist_info


class PlaylistView(View):
    """resolves to /playlist/
    show all playlists indexed
    """

    def get(self, request):
        """handle http get requests"""
        user_id = request.user.id
        view_config = self.read_config(user_id=user_id)

        # handle search
        search_get = request.GET.get("search", False)
        if search_get:
            search_encoded = urllib.parse.quote(search_get)
        else:
            search_encoded = False
        # define page size
        page_get = int(request.GET.get("page", 0))
        pagination_handler = Pagination(
            page_get, user_id, search_get=search_encoded
        )

        url = view_config["es_url"] + "/ta_playlist/_search"
        data = self.build_data(pagination_handler, search_get, view_config)
        search = SearchHandler(url, data)
        playlist_hits = search.get_data()
        pagination_handler.validate(search.max_hits)
        search_form = PlaylistSearchForm()
        subscribe_form = SubscribeToChannelForm()

        context = {
            "subscribe_form": subscribe_form,
            "search_form": search_form,
            "title": "Playlists",
            "colors": view_config["colors"],
            "show_subed_only": view_config["show_subed_only"],
            "pagination": pagination_handler.pagination,
            "playlists": playlist_hits,
            "view_style": view_config["view_style"],
            "running": view_config["running"],
        }
        return render(request, "home/playlist.html", context)

    @staticmethod
    def build_data(pagination_handler, search_get, view_config):
        """build data object for query"""
        data = {
            "size": pagination_handler.pagination["page_size"],
            "from": pagination_handler.pagination["page_from"],
            "query": {
                "term": {"playlist_entries.downloaded": {"value": True}}
            },
            "sort": [{"playlist_name.keyword": {"order": "asc"}}],
        }
        if view_config["show_subed_only"]:
            data["query"] = {"term": {"playlist_subscribed": {"value": True}}}
        if search_get:
            data["query"] = {
                "bool": {
                    "should": [
                        {
                            "multi_match": {
                                "query": search_get,
                                "fields": [
                                    "playlist_channel_id",
                                    "playlist_channel",
                                    "playlist_name",
                                ],
                            }
                        }
                    ],
                    "minimum_should_match": 1,
                }
            }
        return data

    @staticmethod
    def read_config(user_id):
        """read config file"""
        config_handler = AppConfig(user_id)
        view_key = f"{user_id}:view:playlist"
        view_style = RedisArchivist().get_message(view_key)["status"]
        if not view_style:
            view_style = config_handler.config["default_view"]["channel"]

        sub_only_key = f"{user_id}:show_subed_only"
        show_subed_only = RedisArchivist().get_message(sub_only_key)["status"]
        running = RedisArchivist().get_message("progress:subscribe")["status"]

        view_config = {
            "es_url": config_handler.config["application"]["es_url"],
            "colors": config_handler.colors,
            "view_style": view_style,
            "show_subed_only": show_subed_only,
            "running": running,
        }
        return view_config

    @staticmethod
    def post(request):
        """handle post from search form"""
        search_form = PlaylistSearchForm(data=request.POST)
        if search_form.is_valid():
            search_query = request.POST.get("searchInput")
            print(search_query)
            search_url = "/playlist/?" + urlencode({"search": search_query})
            return redirect(search_url, permanent=True)

        subscribe_form = SubscribeToPlaylistForm(data=request.POST)
        if subscribe_form.is_valid():
            url_str = request.POST.get("subscribe")
            print(url_str)
            subscribe_to.delay(url_str)

        sleep(1)
        return redirect("playlist")


class VideoView(View):
    """resolves to /video/<video-id>/
    display details about a single video
    """

    def get(self, request, video_id):
        """get single video"""
        es_url, colors = self.read_config(user_id=request.user.id)
        url = f"{es_url}/ta_video/_doc/{video_id}"
        data = None
        look_up = SearchHandler(url, data)
        video_hit = look_up.get_data()
        video_data = video_hit[0]["source"]
        try:
            rating = video_data["stats"]["average_rating"]
            video_data["stats"]["average_rating"] = self.star_creator(rating)
        except KeyError:
            video_data["stats"]["average_rating"] = False

        if "playlist" in video_data.keys():
            playlists = video_data["playlist"]
            playlist_nav = self.build_playlists(video_id, playlists)
        else:
            playlist_nav = False

        video_title = video_data["title"]
        context = {
            "video": video_data,
            "playlist_nav": playlist_nav,
            "title": video_title,
            "colors": colors,
        }
        return render(request, "home/video.html", context)

    @staticmethod
    def build_playlists(video_id, playlists):
        """build playlist nav if available"""
        all_navs = []
        for playlist_id in playlists:
            handler = YoutubePlaylist(playlist_id)
            handler.get_playlist_dict()
            nav = handler.build_nav(video_id)
            if nav:
                all_navs.append(nav)

        return all_navs

    @staticmethod
    def read_config(user_id):
        """read config file"""
        config_handler = AppConfig(user_id)
        es_url = config_handler.config["application"]["es_url"]
        colors = config_handler.colors
        return es_url, colors

    @staticmethod
    def star_creator(rating):
        """convert rating float to stars"""
        stars = []
        for _ in range(1, 6):
            if rating >= 0.75:
                stars.append("full")
            elif 0.25 < rating < 0.75:
                stars.append("half")
            else:
                stars.append("empty")
            rating = rating - 1
        return stars


class SettingsView(View):
    """resolves to /settings/
    handle the settings page, display current settings,
    take post request from the form to update settings
    """

    @staticmethod
    def get(request):
        """read and display current settings"""
        config_handler = AppConfig(request.user.id)
        colors = config_handler.colors

        user_form = UserSettingsForm()
        app_form = ApplicationSettingsForm()

        context = {
            "title": "Settings",
            "config": config_handler.config,
            "colors": colors,
            "user_form": user_form,
            "app_form": app_form,
        }

        return render(request, "home/settings.html", context)

    @staticmethod
    def post(request):
        """handle form post to update settings"""

        form_response = forms.Form(request.POST)
        if form_response.is_valid():
            form_post = dict(request.POST)
            print(form_post)
            del form_post["csrfmiddlewaretoken"]
            config_handler = AppConfig()
            if "application-settings" in form_post:
                del form_post["application-settings"]
                config_handler.update_config(form_post)
            elif "user-settings" in form_post:
                del form_post["user-settings"]
                config_handler.set_user_config(form_post, request.user.id)

        return redirect("settings", permanent=True)


def progress(request):
    # pylint: disable=unused-argument
    """endpoint for download progress ajax calls"""
    config = AppConfig().config
    cache_dir = config["application"]["cache_dir"]
    json_data = RedisArchivist().get_dl_message(cache_dir)
    return JsonResponse(json_data)


def process(request):
    """handle all the buttons calls via POST ajax"""
    if request.method == "POST":
        current_user = request.user.id
        post_dict = json.loads(request.body.decode())
        post_handler = PostData(post_dict, current_user)
        if post_handler.to_exec:
            task_result = post_handler.run_task()
            return JsonResponse(task_result)

    return JsonResponse({"success": False})
