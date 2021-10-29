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
from django.forms.widgets import PasswordInput, TextInput
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils.http import urlencode
from django.views import View
from home.src.config import AppConfig
from home.src.download import ChannelSubscription, PendingList
from home.src.helper import RedisArchivist, RedisQueue, process_url_list
from home.src.index import WatchState, YoutubeChannel, YoutubeVideo
from home.src.searching import Pagination, SearchForm, SearchHandler
from home.tasks import (
    download_pending,
    download_single,
    extrac_dl,
    kill_dl,
    rescan_filesystem,
    run_backup,
    run_manual_import,
    run_restore_backup,
    update_subscribed,
)


class HomeView(View):
    """resolves to /
    handle home page and video search post functionality
    """

    CONFIG = AppConfig().config
    ES_URL = CONFIG["application"]["es_url"]

    def get(self, request):
        """return home search results"""
        view_config = self.read_config(user_id=request.user.id)
        # handle search
        search_get = request.GET.get("search", False)
        if search_get:
            search_encoded = urllib.parse.quote(search_get)
        else:
            search_encoded = False
        # define page size
        page_get = int(request.GET.get("page", 0))
        pagination_handler = Pagination(page_get, search_encoded)

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
        context = {
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
        config_handler = AppConfig().config
        colors = config_handler["application"]["colors"]

        view_key = f"{user_id}:view:home"
        view_style = RedisArchivist().get_message(view_key)["status"]
        if not view_style:
            view_style = config_handler["default_view"]["home"]

        sort_by = RedisArchivist().get_message("sort_by")
        if sort_by == {"status": False}:
            sort_by = "published"
        sort_order = RedisArchivist().get_message("sort_order")
        if sort_order == {"status": False}:
            sort_order = "desc"

        hide_watched = RedisArchivist().get_message("hide_watched")
        view_config = {
            "colors": colors,
            "view_style": view_style,
            "sort_by": sort_by,
            "sort_order": sort_order,
            "hide_watched": hide_watched,
        }
        return view_config

    @staticmethod
    def post(request):
        """handle post from search form"""
        post_data = dict(request.POST)
        search_query = post_data["videoSearch"][0]
        search_url = "/?" + urlencode({"search": search_query})
        return redirect(search_url, permanent=True)


class CustomAuthForm(AuthenticationForm):
    """better styled login form"""

    username = forms.CharField(
        widget=TextInput(attrs={"placeholder": "Username"}), label=False
    )
    password = forms.CharField(
        widget=PasswordInput(attrs={"placeholder": "Password"}), label=False
    )


class LoginView(View):
    """resolves to /login/
    Greeting and login page
    """

    def get(self, request):
        """handle get requests"""
        failed = bool(request.GET.get("failed"))
        colors = self.read_config()
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

    @staticmethod
    def read_config():
        """read needed values from redis"""
        config_handler = AppConfig().config
        colors = config_handler["application"]["colors"]
        return colors


class AboutView(View):
    """resolves to /about/
    show helpful how to information
    """

    @staticmethod
    def get(request):
        """handle http get"""
        config = AppConfig().config
        colors = config["application"]["colors"]
        context = {"title": "About", "colors": colors}
        return render(request, "home/about.html", context)


class DownloadView(View):
    """resolves to /download/
    takes POST for downloading youtube links
    """

    def get(self, request):
        """handle get requests"""
        view_config = self.read_config(user_id=request.user.id)

        page_get = int(request.GET.get("page", 0))
        pagination_handler = Pagination(page_get)

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

        context = {
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
        config = AppConfig().config
        colors = config["application"]["colors"]

        view_key = f"{user_id}:view:downloads"
        view_style = RedisArchivist().get_message(view_key)["status"]
        if not view_style:
            view_style = config["default_view"]["downloads"]

        ignored = RedisArchivist().get_message(f"{user_id}:show_ignored_only")
        show_ignored_only = ignored["status"]

        es_url = config["application"]["es_url"]

        view_config = {
            "es_url": es_url,
            "colors": colors,
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
        download_post = dict(request.POST)
        if "vid-url" in download_post.keys():
            url_str = download_post["vid-url"]
            try:
                youtube_ids = process_url_list(url_str)
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
        view_config = self.read_config()
        context = self.get_channel_videos(
            request, channel_id_detail, view_config
        )
        context.update(view_config)
        return render(request, "home/channel_id.html", context)

    @staticmethod
    def read_config():
        """read config file"""
        config = AppConfig().config

        sort_by = RedisArchivist().get_message("sort_by")
        if sort_by == {"status": False}:
            sort_by = "published"
        sort_order = RedisArchivist().get_message("sort_order")
        if sort_order == {"status": False}:
            sort_order = "desc"
        hide_watched = RedisArchivist().get_message("hide_watched")

        view_config = {
            "colors": config["application"]["colors"],
            "es_url": config["application"]["es_url"],
            "view_style": config["default_view"]["home"],
            "sort_by": sort_by,
            "sort_order": sort_order,
            "hide_watched": hide_watched,
        }
        # return es_url, colors, view_style
        return view_config

    def get_channel_videos(self, request, channel_id_detail, view_config):
        """get channel from video index"""
        page_get = int(request.GET.get("page", 0))
        pagination_handler = Pagination(page_get)
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

        print(data)

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
        pagination_handler = Pagination(page_get)
        page_size = pagination_handler.pagination["page_size"]
        page_from = pagination_handler.pagination["page_from"]
        # get
        url = view_config["es_url"] + "/ta_channel/_search"
        data = {
            "size": page_size,
            "from": page_from,
            "query": {"match_all": {}},
            "sort": [{"channel_name.keyword": {"order": "asc"}}],
        }
        if view_config["show_subed_only"]:
            data["query"] = {"term": {"channel_subscribed": {"value": True}}}
        search = SearchHandler(url, data)
        channel_hits = search.get_data()
        max_hits = search.max_hits
        pagination_handler.validate(search.max_hits)
        context = {
            "channels": channel_hits,
            "max_hits": max_hits,
            "pagination": pagination_handler.pagination,
            "show_subed_only": view_config["show_subed_only"],
            "title": "Channels",
            "colors": view_config["colors"],
            "view_style": view_config["view_style"],
        }
        return render(request, "home/channel.html", context)

    @staticmethod
    def read_config(user_id):
        """read config file"""
        config = AppConfig().config
        colors = config["application"]["colors"]

        view_key = f"{user_id}:view:channel"
        view_style = RedisArchivist().get_message(view_key)["status"]
        if not view_style:
            view_style = config["default_view"]["channel"]

        sub_only_key = f"{user_id}:show_subed_only"
        show_subed_only = RedisArchivist().get_message(sub_only_key)["status"]

        view_config = {
            "es_url": config["application"]["es_url"],
            "view_style": view_style,
            "show_subed_only": show_subed_only,
            "colors": colors,
        }

        return view_config

    def post(self, request):
        """handle http post requests"""
        subscriptions_post = dict(request.POST)
        print(subscriptions_post)
        subscriptions_post = dict(request.POST)
        if "subscribe" in subscriptions_post.keys():
            sub_str = subscriptions_post["subscribe"]
            try:
                youtube_ids = process_url_list(sub_str)
                self.subscribe_to(youtube_ids)
            except ValueError:
                print("parsing subscribe ids failed!")
                print(sub_str)

        sleep(1)
        return redirect("channel", permanent=True)

    @staticmethod
    def subscribe_to(youtube_ids):
        """process the subscribe ids"""
        for youtube_id in youtube_ids:
            if youtube_id["type"] == "video":
                to_sub = youtube_id["url"]
                vid_details = PendingList().get_youtube_details(to_sub)
                channel_id_sub = vid_details["channel_id"]
            elif youtube_id["type"] == "channel":
                channel_id_sub = youtube_id["url"]
            else:
                raise ValueError("failed to subscribe to: " + youtube_id)

            ChannelSubscription().change_subscribe(
                channel_id_sub, channel_subscribed=True
            )
            print("subscribed to: " + channel_id_sub)


class VideoView(View):
    """resolves to /video/<video-id>/
    display details about a single video
    """

    def get(self, request, video_id):
        """get single video"""
        es_url, colors = self.read_config()
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

        video_title = video_data["title"]
        context = {"video": video_data, "title": video_title, "colors": colors}
        return render(request, "home/video.html", context)

    @staticmethod
    def read_config():
        """read config file"""
        config = AppConfig().config
        es_url = config["application"]["es_url"]
        colors = config["application"]["colors"]
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
        config = AppConfig().config
        colors = config["application"]["colors"]

        context = {"title": "Settings", "config": config, "colors": colors}

        return render(request, "home/settings.html", context)

    @staticmethod
    def post(request):
        """handle form post to update settings"""
        form_post = dict(request.POST)
        del form_post["csrfmiddlewaretoken"]
        print(form_post)
        config_handler = AppConfig()
        config_handler.update_config(form_post)

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


class PostData:
    """
    map frontend http post values to backend funcs
    handover long running tasks to celery
    """

    def __init__(self, post_dict, current_user):
        self.post_dict = post_dict
        self.to_exec, self.exec_val = list(post_dict.items())[0]
        self.current_user = current_user

    def run_task(self):
        """execute and return task result"""
        to_exec = self.exec_map()
        task_result = to_exec()
        return task_result

    def exec_map(self):
        """map dict key and return function to execute"""
        exec_map = {
            "watched": self.watched,
            "un_watched": self.un_watched,
            "change_view": self.change_view,
            "rescan_pending": self.rescan_pending,
            "ignore": self.ignore,
            "dl_pending": self.dl_pending,
            "queue": self.queue_handler,
            "unsubscribe": self.unsubscribe,
            "sort_order": self.sort_order,
            "hide_watched": self.hide_watched,
            "show_subed_only": self.show_subed_only,
            "dlnow": self.dlnow,
            "show_ignored_only": self.show_ignored_only,
            "forgetIgnore": self.forget_ignore,
            "addSingle": self.add_single,
            "manual-import": self.manual_import,
            "db-backup": self.db_backup,
            "db-restore": self.db_restore,
            "fs-rescan": self.fs_rescan,
            "channel-search": self.channel_search,
            "delete-video": self.delete_video,
            "delete-channel": self.delete_channel,
        }

        return exec_map[self.to_exec]

    def watched(self):
        """mark as watched"""
        WatchState(self.exec_val).mark_as_watched()
        return {"success": True}

    def un_watched(self):
        """mark as unwatched"""
        WatchState(self.exec_val).mark_as_unwatched()
        return {"success": True}

    def change_view(self):
        """process view changes in home, channel, and downloads"""
        origin, new_view = self.exec_val.split(":")
        key = f"{self.current_user}:view:{origin}"
        print(f"change view: {key} to {new_view}")
        RedisArchivist().set_message(key, {"status": new_view}, expire=False)
        return {"success": True}

    @staticmethod
    def rescan_pending():
        """look for new items in subscribed channels"""
        print("rescan subscribed channels")
        update_subscribed.delay()
        return {"success": True}

    def ignore(self):
        """ignore from download queue"""
        id_to_ignore = self.exec_val
        print("ignore video " + id_to_ignore)
        handler = PendingList()
        handler.ignore_from_pending([id_to_ignore])
        # also clear from redis queue
        RedisQueue("dl_queue").clear_item(id_to_ignore)
        return {"success": True}

    @staticmethod
    def dl_pending():
        """start the download queue"""
        print("download pending")
        running = download_pending.delay()
        task_id = running.id
        print("set task id: " + task_id)
        RedisArchivist().set_message("dl_queue_id", task_id, expire=False)
        return {"success": True}

    def queue_handler(self):
        """queue controls from frontend"""
        to_execute = self.exec_val
        if to_execute == "stop":
            print("stopping download queue")
            RedisQueue("dl_queue").clear()
        elif to_execute == "kill":
            task_id = RedisArchivist().get_message("dl_queue_id")
            if not isinstance(task_id, str):
                task_id = False
            else:
                print("brutally killing " + task_id)
            kill_dl(task_id)

        return {"success": True}

    def unsubscribe(self):
        """unsubscribe from channel"""
        channel_id_unsub = self.exec_val
        print("unsubscribe from " + channel_id_unsub)
        ChannelSubscription().change_subscribe(
            channel_id_unsub, channel_subscribed=False
        )
        return {"success": True}

    def sort_order(self):
        """change the sort between published to downloaded"""
        sort_order = self.exec_val
        if sort_order in ["asc", "desc"]:
            RedisArchivist().set_message(
                "sort_order", sort_order, expire=False
            )
        else:
            RedisArchivist().set_message("sort_by", sort_order, expire=False)
        return {"success": True}

    def hide_watched(self):
        """toggle if to show watched vids or not"""
        hide_watched = bool(int(self.exec_val))
        print(f"hide watched: {hide_watched}")
        RedisArchivist().set_message(
            "hide_watched", hide_watched, expire=False
        )
        return {"success": True}

    def show_subed_only(self):
        """show or hide subscribed channels only on channels page"""
        key = f"{self.current_user}:show_subed_only"
        message = {"status": bool(int(self.exec_val))}
        print(f"show {key}: {message}")
        RedisArchivist().set_message(key, message, expire=False)
        return {"success": True}

    def dlnow(self):
        """start downloading single vid now"""
        youtube_id = self.exec_val
        print("downloading: " + youtube_id)
        running = download_single.delay(youtube_id=youtube_id)
        task_id = running.id
        print("set task id: " + task_id)
        RedisArchivist().set_message("dl_queue_id", task_id, expire=False)
        return {"success": True}

    def show_ignored_only(self):
        """switch view on /downloads/ to show ignored only"""
        show_value = self.exec_val
        key = f"{self.current_user}:show_ignored_only"
        value = {"status": show_value}
        print(f"Filter download view ignored only: {show_value}")
        RedisArchivist().set_message(key, value, expire=False)
        return {"success": True}

    def forget_ignore(self):
        """delete from ta_download index"""
        youtube_id = self.exec_val
        print("forgetting from download index: " + youtube_id)
        PendingList().delete_from_pending(youtube_id)
        return {"success": True}

    def add_single(self):
        """add single youtube_id to download queue"""
        youtube_id = self.exec_val
        print("add vid to dl queue: " + youtube_id)
        PendingList().delete_from_pending(youtube_id)
        youtube_ids = process_url_list([youtube_id])
        extrac_dl.delay(youtube_ids)
        return {"success": True}

    @staticmethod
    def manual_import():
        """run manual import from settings page"""
        print("starting manual import")
        run_manual_import.delay()
        return {"success": True}

    @staticmethod
    def db_backup():
        """backup es to zip from settings page"""
        print("backing up database")
        run_backup.delay()
        return {"success": True}

    @staticmethod
    def db_restore():
        """restore es zip from settings page"""
        print("restoring index from backup zip")
        run_restore_backup.delay()
        return {"success": True}

    @staticmethod
    def fs_rescan():
        """start file system rescan task"""
        print("start filesystem scan")
        rescan_filesystem.delay()
        return {"success": True}

    def channel_search(self):
        """search for channel name as_you_type"""
        search_query = self.exec_val
        print("searching for: " + search_query)
        search_results = SearchForm().search_channels(search_query)
        return search_results

    def delete_video(self):
        """delete media file, metadata and thumb"""
        youtube_id = self.exec_val
        YoutubeVideo(youtube_id).delete_media_file()
        return {"success": True}

    def delete_channel(self):
        """delete channel and all matching videos"""
        channel_id = self.exec_val
        YoutubeChannel(channel_id).delete_channel()
        return {"success": True}
