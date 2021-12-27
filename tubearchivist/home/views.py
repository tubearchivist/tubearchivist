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
    SchedulerSettingsForm,
    SubscribeToChannelForm,
    SubscribeToPlaylistForm,
    UserSettingsForm,
    VideoSearchForm,
)
from home.src.config import AppConfig, ScheduleBuilder
from home.src.frontend import PostData
from home.src.helper import RedisArchivist, UrlListParser
from home.src.index import YoutubePlaylist
from home.src.index_management import get_available_backups
from home.src.searching import Pagination, SearchHandler
from home.tasks import extrac_dl, subscribe_to


class ArchivistViewConfig(View):
    """base view class to generate initial config context"""

    def __init__(self, view_origin):
        super().__init__()
        self.view_origin = view_origin
        self.user_id = False
        self.user_conf = False
        self.default_conf = False
        self.context = False

    def _get_sort_by(self):
        """return sort_by config var"""
        messag_key = f"{self.user_id}:sort_by"
        sort_by = self.user_conf.get_message(messag_key)["status"]
        if not sort_by:
            sort_by = self.default_conf["archive"]["sort_by"]

        return sort_by

    def _get_sort_order(self):
        """return sort_order config var"""
        sort_order_key = f"{self.user_id}:sort_order"
        sort_order = self.user_conf.get_message(sort_order_key)["status"]
        if not sort_order:
            sort_order = self.default_conf["archive"]["sort_order"]

        return sort_order

    def _get_view_style(self):
        """return view_style config var"""
        view_key = f"{self.user_id}:view:{self.view_origin}"
        view_style = self.user_conf.get_message(view_key)["status"]
        if not view_style:
            view_style = self.default_conf["default_view"][self.view_origin]

        return view_style

    def _get_hide_watched(self):
        hide_watched_key = f"{self.user_id}:hide_watched"
        hide_watched = self.user_conf.get_message(hide_watched_key)["status"]

        return hide_watched

    def _get_show_ignore_only(self):
        ignored_key = f"{self.user_id}:show_ignored_only"
        show_ignored_only = self.user_conf.get_message(ignored_key)["status"]

        return show_ignored_only

    def _get_show_subed_only(self):
        sub_only_key = f"{self.user_id}:show_subed_only"
        show_subed_only = self.user_conf.get_message(sub_only_key)["status"]

        return show_subed_only

    def config_builder(self, user_id):
        """build default context for every view"""
        self.user_id = user_id
        self.user_conf = RedisArchivist()
        self.default_conf = AppConfig().config

        self.context = {
            "colors": self.default_conf["application"]["colors"],
            "sort_by": self._get_sort_by(),
            "sort_order": self._get_sort_order(),
            "view_style": self._get_view_style(),
            "hide_watched": self._get_hide_watched(),
            "show_ignored_only": self._get_show_ignore_only(),
            "show_subed_only": self._get_show_subed_only(),
        }


class ArchivistResultsView(ArchivistViewConfig):
    """View class to inherit from when searching data in es"""

    view_origin = False
    es_search = False

    def __init__(self):
        super().__init__(self.view_origin)
        self.pagination_handler = False
        self.search_get = False
        self.data = False
        self.sort_by = False

    def _sort_by_overwrite(self):
        """overwrite sort by key to match with es keys"""
        sort_by_map = {
            "views": "stats.view_count",
            "likes": "stats.like_count",
            "downloaded": "date_downloaded",
            "published": "published",
        }
        sort_by = sort_by_map[self.context["sort_by"]]

        return sort_by

    @staticmethod
    def _url_encode(search_get):
        """url encode search form request"""
        if search_get:
            search_encoded = urllib.parse.quote(search_get)
        else:
            search_encoded = False

        return search_encoded

    def _initial_data(self):
        """add initial data dict"""
        sort_order = self.context["sort_order"]
        data = {
            "size": self.pagination_handler.pagination["page_size"],
            "from": self.pagination_handler.pagination["page_from"],
            "query": {"match_all": {}},
            "sort": [{self.sort_by: {"order": sort_order}}],
        }
        self.data = data

    def initiate_vars(self, page_get, user_id, search_get=False):
        """search in es for vidoe hits"""
        self.user_id = user_id
        self.config_builder(self.user_id)
        self.search_get = search_get
        self.pagination_handler = Pagination(
            page_get, self.user_id, search_get=self._url_encode(search_get)
        )
        self.sort_by = self._sort_by_overwrite()
        self._initial_data()

    def find_results(self):
        """add results and pagination to context"""
        url = self.default_conf["application"]["es_url"] + self.es_search
        search = SearchHandler(url, self.data)
        self.context["results"] = search.get_data()
        self.pagination_handler.validate(search.max_hits)
        self.context["max_hits"] = search.max_hits
        self.context["pagination"] = self.pagination_handler.pagination


class HomeView(ArchivistResultsView):
    """resolves to /
    handle home page and video search post functionality
    """

    view_origin = "home"
    es_search = "/ta_video/_search"

    def get(self, request):
        """handle get requests"""
        user_id = request.user.id
        page_get = int(request.GET.get("page", 0))
        search_get = request.GET.get("search", False)

        self.initiate_vars(page_get, user_id, search_get)
        self._update_view_data()
        self.find_results()

        self.context.update({"search_form": VideoSearchForm()})

        return render(request, "home/home.html", self.context)

    def _update_view_data(self):
        """update view specific data dict"""
        if self.context["hide_watched"]:
            self.data["query"] = {"term": {"player.watched": {"value": False}}}
        if self.search_get:
            del self.data["sort"]
            query = {
                "multi_match": {
                    "query": self.search_get,
                    "fields": ["title", "channel.channel_name", "tags"],
                    "type": "cross_fields",
                    "operator": "and",
                }
            }
            self.data["query"] = query

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

    SEC_IN_DAY = 60 * 60 * 24

    @staticmethod
    def get(request):
        """handle get requests"""
        failed = bool(request.GET.get("failed"))
        colors = AppConfig(request.user.id).colors
        form = CustomAuthForm()
        context = {"colors": colors, "form": form, "form_error": failed}
        return render(request, "home/login.html", context)

    def post(self, request):
        """handle login post request"""
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            remember_me = request.POST.get("remember_me") or False
            if remember_me == "on":
                request.session.set_expiry(self.SEC_IN_DAY * 365)
            else:
                request.session.set_expiry(self.SEC_IN_DAY * 2)
            print(f"expire session in {request.session.get_expiry_age()} secs")

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


class DownloadView(ArchivistResultsView):
    """resolves to /download/
    takes POST for downloading youtube links
    """

    view_origin = "downloads"
    es_search = "/ta_download/_search"

    def get(self, request):
        """handle get request"""
        user_id = request.user.id
        page_get = int(request.GET.get("page", 0))

        self.initiate_vars(page_get, user_id)
        self._update_view_data()
        self.find_results()

        self.context.update(
            {
                "title": "Downloads",
                "add_form": AddToQueueForm(),
            }
        )
        return render(request, "home/downloads.html", self.context)

    def _update_view_data(self):
        """update downloads view specific data dict"""
        if self.context["show_ignored_only"]:
            filter_view = "ignore"
        else:
            filter_view = "pending"
        self.data.update(
            {
                "query": {"term": {"status": {"value": filter_view}}},
                "sort": [{"timestamp": {"order": "asc"}}],
            }
        )

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
                    "status": "message:add",
                    "level": "error",
                    "title": "Failed to extract links.",
                    "message": "Not a video, channel or playlist ID or URL",
                }
                RedisArchivist().set_message("message:add", mess_dict)
                return redirect("downloads")

            print(youtube_ids)
            extrac_dl.delay(youtube_ids)

        sleep(2)
        return redirect("downloads", permanent=True)


class ChannelIdView(ArchivistResultsView):
    """resolves to /channel/<channel-id>/
    display single channel page from channel_id
    """

    view_origin = "home"
    es_search = "/ta_video/_search"

    def get(self, request, channel_id):
        """get request"""
        user_id = request.user.id
        page_get = int(request.GET.get("page", 0))
        self.initiate_vars(page_get, user_id)
        self._update_view_data(channel_id)
        self.find_results()

        if self.context["results"]:
            channel_info = self.context["results"][0]["source"]["channel"]
            channel_name = channel_info["channel_name"]
        else:
            channel_info, channel_name = self.get_channel_info(channel_id)

        self.context.update(
            {
                "title": "Channel: " + channel_name,
                "channel_info": channel_info,
            }
        )

        return render(request, "home/channel_id.html", self.context)

    def _update_view_data(self, channel_id):
        """update view specific data dict"""
        query = {
            "bool": {
                "must": [
                    {"term": {"channel.channel_id": {"value": channel_id}}}
                ]
            }
        }
        self.data["query"] = query

        if self.context["hide_watched"]:
            to_append = {"term": {"player.watched": {"value": False}}}
            self.data["query"]["bool"]["must"].append(to_append)

    def get_channel_info(self, channel_id):
        """fallback channel info if no videos found"""
        es_url = self.default_conf["application"]["es_url"]
        url = f"{es_url}/ta_channel/_doc/{channel_id}"
        search = SearchHandler(url, data=False)
        channel_data = search.get_data()
        channel_info = channel_data[0]["source"]
        channel_name = channel_info["channel_name"]
        return channel_info, channel_name


class ChannelView(ArchivistResultsView):
    """resolves to /channel/
    handle functionality for channel overview page, subscribe to channel,
    search as you type for channel name
    """

    view_origin = "channel"
    es_search = "/ta_channel/_search"

    def get(self, request):
        """handle get request"""
        user_id = request.user.id
        page_get = int(request.GET.get("page", 0))

        self.initiate_vars(page_get, user_id)
        self._update_view_data()
        self.find_results()
        self.context.update(
            {
                "title": "Channels",
                "search_form": ChannelSearchForm(),
                "subscribe_form": SubscribeToChannelForm(),
            }
        )

        return render(request, "home/channel.html", self.context)

    def _update_view_data(self):
        """update view data dict"""
        self.data["sort"] = [{"channel_name.keyword": {"order": "asc"}}]
        if self.context["show_subed_only"]:
            self.data["query"] = {
                "term": {"channel_subscribed": {"value": True}}
            }

    @staticmethod
    def post(request):
        """handle http post requests"""
        subscribe_form = SubscribeToChannelForm(data=request.POST)
        if subscribe_form.is_valid():
            message = {
                "status": "message:subchannel",
                "level": "info",
                "title": "Subscribing to Channels",
                "message": "Parsing form data",
            }
            RedisArchivist().set_message("message:subchannel", message=message)
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
            "query": {"match_all": {}},
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
            message = {
                "status": "message:subplaylist",
                "level": "info",
                "title": "Subscribing to Playlists",
                "message": "Parsing form data",
            }
            RedisArchivist().set_message(
                "message:subplaylist", message=message
            )
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
        if not rating:
            return False

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

        available_backups = get_available_backups()
        user_form = UserSettingsForm()
        app_form = ApplicationSettingsForm()
        scheduler_form = SchedulerSettingsForm()

        context = {
            "title": "Settings",
            "config": config_handler.config,
            "colors": colors,
            "available_backups": available_backups,
            "user_form": user_form,
            "app_form": app_form,
            "scheduler_form": scheduler_form,
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
            elif "scheduler-settings" in form_post:
                del form_post["scheduler-settings"]
                print(form_post)
                ScheduleBuilder().update_schedule_conf(form_post)

        sleep(1)
        return redirect("settings", permanent=True)


def progress(request):
    # pylint: disable=unused-argument
    """resolves to /progress/
    return list of messages for frontend
    """
    all_messages = RedisArchivist().get_progress()
    json_data = {"messages": all_messages}
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
