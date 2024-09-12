"""
Functionality:
- all views for home app
- holds base classes to inherit from
"""

import enum
import urllib.parse
import uuid
from time import sleep

from api.src.search_processor import SearchProcess, process_aggs
from api.views import check_admin
from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.http import Http404
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.views import View
from home.models import CustomPeriodicTask
from home.src.download.queue import PendingInteract
from home.src.download.yt_dlp_base import CookieHandler
from home.src.es.backup import ElasticBackup
from home.src.es.connect import ElasticWrap
from home.src.es.snapshot import ElasticSnapshot
from home.src.frontend.forms import (
    AddToQueueForm,
    ApplicationSettingsForm,
    ChannelOverwriteForm,
    CreatePlaylistForm,
    CustomAuthForm,
    MultiSearchForm,
    SubscribeToChannelForm,
    SubscribeToPlaylistForm,
    UserSettingsForm,
)
from home.src.frontend.forms_schedule import (
    NotificationSettingsForm,
    SchedulerSettingsForm,
)
from home.src.index.channel import channel_overwrites
from home.src.index.generic import Pagination
from home.src.index.playlist import YoutubePlaylist
from home.src.index.reindex import ReindexProgress
from home.src.index.video_constants import VideoTypeEnum
from home.src.ta.config import AppConfig, ReleaseVersion
from home.src.ta.config_schedule import ScheduleBuilder
from home.src.ta.helper import check_stylesheet, time_parser
from home.src.ta.notify import Notifications, get_all_notifications
from home.src.ta.settings import EnvironmentSettings
from home.src.ta.ta_redis import RedisArchivist
from home.src.ta.users import UserConfig
from home.tasks import index_channel_playlists, subscribe_to
from rest_framework.authtoken.models import Token


class ArchivistViewConfig(View):
    """base view class to generate initial config context"""

    def __init__(self, view_origin):
        super().__init__()
        self.view_origin = view_origin
        self.user_id = False
        self.user_conf: UserConfig = False
        self.context = False

    def get_all_view_styles(self):
        """get dict of all view styles for search form"""
        all_styles = {}
        for view_origin in ["channel", "playlist", "home", "downloads"]:
            all_styles[view_origin] = self.user_conf.get_value(
                f"view_style_{view_origin}"
            )

        return all_styles

    def config_builder(self, user_id):
        """build default context for every view"""
        self.user_id = user_id
        self.user_conf = UserConfig(self.user_id)

        self.context = {
            "stylesheet": check_stylesheet(
                self.user_conf.get_value("stylesheet")
            ),
            "cast": EnvironmentSettings.ENABLE_CAST,
            "sort_by": self.user_conf.get_value("sort_by"),
            "sort_order": self.user_conf.get_value("sort_order"),
            "view_style": self.user_conf.get_value(
                f"view_style_{self.view_origin}"
            ),
            "grid_items": self.user_conf.get_value("grid_items"),
            "hide_watched": self.user_conf.get_value("hide_watched"),
            "show_ignored_only": self.user_conf.get_value("show_ignored_only"),
            "show_subed_only": self.user_conf.get_value("show_subed_only"),
            "version": settings.TA_VERSION,
            "ta_update": ReleaseVersion().get_update(),
        }


class ArchivistResultsView(ArchivistViewConfig):
    """View class to inherit from when searching data in es"""

    view_origin = ""
    es_search = ""

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
            "duration": "player.duration",
            "filesize": "media_size",
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

    def match_progress(self):
        """add video progress to result context"""
        results = RedisArchivist().list_items(f"{self.user_id}:progress:")
        if not results or not self.context["results"]:
            return

        self.context["continue_vids"] = self.get_in_progress(results)

        in_progress = {i["youtube_id"]: i["position"] for i in results}
        for video in self.context["results"]:
            if video["youtube_id"] in in_progress:
                played_sec = in_progress.get(video["youtube_id"])
                total = video["player"]["duration"]
                if not total:
                    total = played_sec * 2
                video["player"]["progress"] = 100 * (played_sec / total)

    def get_in_progress(self, results):
        """get all videos in progress"""
        ids = [{"match": {"youtube_id": i.get("youtube_id")}} for i in results]
        data = {
            "size": UserConfig(self.user_id).get_value("page_size"),
            "query": {"bool": {"should": ids}},
            "sort": [{"published": {"order": "desc"}}],
        }
        response, _ = ElasticWrap("ta_video/_search").get(data)
        videos = SearchProcess(response).process()

        if not videos:
            return False

        for video in videos:
            youtube_id = video["youtube_id"]
            matched = [i for i in results if i["youtube_id"] == youtube_id]
            played_sec = matched[0]["position"]
            total = video["player"]["duration"]
            if not total:
                total = matched[0].get("position") * 2
            video["player"]["progress"] = 100 * (played_sec / total)

        return videos

    def single_lookup(self, es_path):
        """retrieve a single item from url"""
        response, status_code = ElasticWrap(es_path).get()
        if not status_code == 200:
            raise Http404

        result = SearchProcess(response).process()

        return result

    def initiate_vars(self, request):
        """search in es for vidoe hits"""
        self.user_id = request.user.id
        self.config_builder(self.user_id)
        self.search_get = request.GET.get("search", False)
        self.pagination_handler = Pagination(request)
        self.sort_by = self._sort_by_overwrite()
        self._initial_data()

    def find_results(self):
        """add results and pagination to context"""
        response, _ = ElasticWrap(self.es_search).get(self.data)
        process_aggs(response)
        results = SearchProcess(response).process()
        max_hits = response["hits"]["total"]["value"]
        self.pagination_handler.validate(max_hits)
        self.context.update(
            {
                "results": results,
                "max_hits": max_hits,
                "pagination": self.pagination_handler.pagination,
                "aggs": response.get("aggregations"),
            }
        )


class MinView(View):
    """to inherit from for minimal config vars"""

    @staticmethod
    def get_min_context(request):
        """build minimal vars for context"""
        return {
            "stylesheet": check_stylesheet(
                UserConfig(request.user.id).get_value("stylesheet")
            ),
            "version": settings.TA_VERSION,
            "ta_update": ReleaseVersion().get_update(),
        }


class HomeView(ArchivistResultsView):
    """resolves to /
    handle home page and video search post functionality
    """

    view_origin = "home"
    es_search = "ta_video/_search"

    def get(self, request):
        """handle get requests"""
        self.initiate_vars(request)
        self._update_view_data()
        self.find_results()
        self.match_progress()

        return render(request, "home/home.html", self.context)

    def _update_view_data(self):
        """update view specific data dict"""
        self.data["sort"].extend(
            [
                {"channel.channel_name.keyword": {"order": "asc"}},
                {"title.keyword": {"order": "asc"}},
            ]
        )

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


class LoginView(MinView):
    """resolves to /login/
    Greeting and login page
    """

    SEC_IN_DAY = 60 * 60 * 24

    def get(self, request):
        """handle get requests"""
        context = self.get_min_context(request)
        context.update(
            {
                "form": CustomAuthForm(),
                "form_error": bool(request.GET.get("failed")),
            }
        )

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


class AboutView(MinView):
    """resolves to /about/
    show helpful how to information
    """

    def get(self, request):
        """handle http get"""
        context = self.get_min_context(request)
        context.update({"title": "About"})
        return render(request, "home/about.html", context)


@method_decorator(user_passes_test(check_admin), name="dispatch")
class DownloadView(ArchivistResultsView):
    """resolves to /download/
    handle the download queue
    """

    view_origin = "downloads"
    es_search = "ta_download/_search"

    def get(self, request):
        """handle get request"""
        self.initiate_vars(request)
        filter_view = self._update_view_data(request)
        self.find_results()
        self.context.update(
            {
                "title": "Downloads",
                "add_form": AddToQueueForm(),
                "channel_agg_list": self._get_channel_agg(filter_view),
            }
        )
        return render(request, "home/downloads.html", self.context)

    def _update_view_data(self, request):
        """update downloads view specific data dict"""
        if self.context["show_ignored_only"]:
            filter_view = "ignore"
        else:
            filter_view = "pending"

        must_list = [{"term": {"status": {"value": filter_view}}}]

        channel_filter = request.GET.get("channel", False)
        if channel_filter:
            must_list.append(
                {"term": {"channel_id": {"value": channel_filter}}}
            )

            channel = PendingInteract(channel_filter).get_channel()
            self.context.update(
                {
                    "channel_filter_id": channel.get("channel_id"),
                    "channel_filter_name": channel.get("channel_name"),
                }
            )

        self.data.update(
            {
                "query": {"bool": {"must": must_list}},
                "sort": [
                    {"auto_start": {"order": "desc"}},
                    {"timestamp": {"order": "asc"}},
                ],
            }
        )

        return filter_view

    def _get_channel_agg(self, filter_view):
        """get pending channel with count"""
        data = {
            "size": 0,
            "query": {"term": {"status": {"value": filter_view}}},
            "aggs": {
                "channel_downloads": {
                    "multi_terms": {
                        "size": 30,
                        "terms": [
                            {"field": "channel_name.keyword"},
                            {"field": "channel_id"},
                        ],
                        "order": {"_count": "desc"},
                    }
                }
            },
        }
        response, _ = ElasticWrap(self.es_search).get(data=data)
        buckets = response["aggregations"]["channel_downloads"]["buckets"]

        buckets_sorted = []
        for i in buckets:
            bucket = {
                "name": i["key"][0],
                "id": i["key"][1],
                "count": i["doc_count"],
            }
            buckets_sorted.append(bucket)

        return buckets_sorted


class ChannelIdBaseView(ArchivistResultsView):
    """base class for all channel-id views"""

    def get_channel_meta(self, channel_id):
        """get metadata for channel"""
        path = f"ta_channel/_doc/{channel_id}"
        response, _ = ElasticWrap(path).get()
        channel_info = SearchProcess(response).process()
        if not channel_info:
            raise Http404

        return channel_info

    def channel_pages(self, channel_id):
        """get additional context for channel pages"""
        self.channel_has_pending(channel_id)
        self.channel_has_streams(channel_id)
        self.channel_has_shorts(channel_id)
        self.channel_has_playlist(channel_id)

    def channel_has_pending(self, channel_id):
        """check if channel has pending videos in queue"""
        path = "ta_download/_search"
        data = {
            "size": 1,
            "query": {
                "bool": {
                    "must": [
                        {"term": {"status": {"value": "pending"}}},
                        {"term": {"channel_id": {"value": channel_id}}},
                    ]
                }
            },
            "_source": False,
        }
        response, _ = ElasticWrap(path).get(data=data)

        self.context.update({"has_pending": bool(response["hits"]["hits"])})

    def channel_has_streams(self, channel_id):
        """check if channel has streams videos"""
        data = self.get_type_data("streams", channel_id)
        response, _ = ElasticWrap("ta_video/_search").get(data=data)

        self.context.update({"has_streams": bool(response["hits"]["hits"])})

    def channel_has_shorts(self, channel_id):
        """check if channel has shorts videos"""
        data = self.get_type_data("shorts", channel_id)
        response, _ = ElasticWrap("ta_video/_search").get(data=data)

        self.context.update({"has_shorts": bool(response["hits"]["hits"])})

    @staticmethod
    def get_type_data(vid_type, channel):
        """build data query for vid_type"""
        return {
            "size": 1,
            "query": {
                "bool": {
                    "must": [
                        {"term": {"vid_type": {"value": vid_type}}},
                        {"term": {"channel.channel_id": {"value": channel}}},
                    ]
                }
            },
            "_source": False,
        }

    def channel_has_playlist(self, channel_id):
        """check if channel has any playlist indexed"""
        path = "ta_playlist/_search"
        data = {
            "size": 1,
            "query": {"term": {"playlist_channel_id": {"value": channel_id}}},
            "_source": False,
        }
        response, _ = ElasticWrap(path).get(data=data)
        self.context.update({"has_playlists": bool(response["hits"]["hits"])})


class ChannelIdView(ChannelIdBaseView):
    """resolves to /channel/<channel-id>/
    display single channel page from channel_id
    """

    view_origin = "home"
    es_search = "ta_video/_search"
    video_types = [VideoTypeEnum.VIDEOS]

    def get(self, request, channel_id):
        """get request"""
        self.initiate_vars(request)
        self._update_view_data(channel_id)
        self.find_results()
        self.match_progress()
        self.channel_pages(channel_id)

        if self.context["results"]:
            channel_info = self.context["results"][0]["channel"]
            channel_name = channel_info["channel_name"]
        else:
            # fall back channel lookup if no videos found
            es_path = f"ta_channel/_doc/{channel_id}"
            channel_info = self.single_lookup(es_path)
            channel_name = channel_info["channel_name"]

        self.context.update(
            {
                "title": f"Channel: {channel_name}",
                "channel_info": channel_info,
            }
        )

        return render(request, "home/channel_id.html", self.context)

    def _update_view_data(self, channel_id):
        """update view specific data dict"""
        vid_type_terms = []
        for t in self.video_types:
            if t and isinstance(t, enum.Enum):
                vid_type_terms.append(t.value)
            else:
                print(
                    "Invalid value passed into video_types on "
                    + f"ChannelIdView: {t}"
                )
        self.data["query"] = {
            "bool": {
                "must": [
                    {"term": {"channel.channel_id": {"value": channel_id}}},
                    {"terms": {"vid_type": vid_type_terms}},
                ]
            }
        }
        self.data["aggs"] = {
            "total_items": {"value_count": {"field": "youtube_id"}},
            "total_size": {"sum": {"field": "media_size"}},
            "total_duration": {"sum": {"field": "player.duration"}},
        }
        self.data["sort"].append({"title.keyword": {"order": "asc"}})

        if self.context["hide_watched"]:
            to_append = {"term": {"player.watched": {"value": False}}}
            self.data["query"]["bool"]["must"].append(to_append)


class ChannelIdLiveView(ChannelIdView):
    """resolves to /channel/<channel-id>/streams/
    display single channel page from channel_id
    """

    video_types = [VideoTypeEnum.STREAMS]


class ChannelIdShortsView(ChannelIdView):
    """resolves to /channel/<channel-id>/shorts/
    display single channel page from channel_id
    """

    video_types = [VideoTypeEnum.SHORTS]


class ChannelIdAboutView(ChannelIdBaseView):
    """resolves to /channel/<channel-id>/about/
    show metadata, handle per channel conf
    """

    view_origin = "channel"

    def get(self, request, channel_id):
        """handle get request"""
        self.initiate_vars(request)
        self.channel_pages(channel_id)

        response, _ = ElasticWrap(f"ta_channel/_doc/{channel_id}").get()
        channel_info = SearchProcess(response).process()
        reindex = ReindexProgress(
            request_type="channel", request_id=channel_id
        ).get_progress()

        self.context.update(
            {
                "title": "Channel: About " + channel_info["channel_name"],
                "channel_info": channel_info,
                "channel_overwrite_form": ChannelOverwriteForm,
                "reindex": reindex.get("state"),
            }
        )

        return render(request, "home/channel_id_about.html", self.context)

    @method_decorator(user_passes_test(check_admin), name="dispatch")
    @staticmethod
    def post(request, channel_id):
        """handle post request"""
        print(f"handle post from {channel_id}")
        channel_overwrite_form = ChannelOverwriteForm(request.POST)
        if channel_overwrite_form.is_valid():
            overwrites = channel_overwrite_form.cleaned_data
            print(f"{channel_id}: set overwrites {overwrites}")
            channel_overwrites(channel_id, overwrites=overwrites)
            if overwrites.get("index_playlists") == "1":
                index_channel_playlists.delay(channel_id)

        sleep(1)
        return redirect("channel_id_about", channel_id, permanent=True)


class ChannelIdPlaylistView(ChannelIdBaseView):
    """resolves to /channel/<channel-id>/playlist/
    show all playlists of channel
    """

    view_origin = "playlist"
    es_search = "ta_playlist/_search"

    def get(self, request, channel_id):
        """handle get request"""
        self.initiate_vars(request)
        self._update_view_data(channel_id)
        self.find_results()
        self.channel_pages(channel_id)

        channel_info = self.get_channel_meta(channel_id)
        channel_name = channel_info["channel_name"]
        self.context.update(
            {
                "title": "Channel: Playlists " + channel_name,
                "channel_info": channel_info,
            }
        )

        return render(request, "home/channel_id_playlist.html", self.context)

    def _update_view_data(self, channel_id):
        """update view specific data dict"""
        self.data["sort"] = [{"playlist_name.keyword": {"order": "asc"}}]
        must_list = [{"match": {"playlist_channel_id": channel_id}}]

        if self.context["show_subed_only"]:
            must_list.append({"match": {"playlist_subscribed": True}})

        self.data["query"] = {"bool": {"must": must_list}}


class ChannelView(ArchivistResultsView):
    """resolves to /channel/
    handle functionality for channel overview page, subscribe to channel,
    search as you type for channel name
    """

    view_origin = "channel"
    es_search = "ta_channel/_search"

    def get(self, request):
        """handle get request"""
        self.initiate_vars(request)
        self._update_view_data()
        self.find_results()
        self.context.update(
            {
                "title": "Channels",
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

    @method_decorator(user_passes_test(check_admin), name="dispatch")
    @staticmethod
    def post(request):
        """handle http post requests"""
        subscribe_form = SubscribeToChannelForm(data=request.POST)
        if subscribe_form.is_valid():
            url_str = request.POST.get("subscribe")
            print(url_str)
            subscribe_to.delay(url_str, expected_type="channel")

        sleep(1)
        return redirect("channel", permanent=True)


class PlaylistIdView(ArchivistResultsView):
    """resolves to /playlist/<playlist_id>
    show all videos in a playlist
    """

    view_origin = "home"
    es_search = "ta_video/_search"

    def get(self, request, playlist_id):
        """handle get request"""
        self.initiate_vars(request)
        playlist_info, channel_info = self._get_info(playlist_id)
        if not playlist_info:
            raise Http404

        playlist_name = playlist_info["playlist_name"]
        self._update_view_data(playlist_id, playlist_info)
        self.find_results()
        self.match_progress()
        reindex = ReindexProgress(
            request_type="playlist", request_id=playlist_id
        ).get_progress()

        self.context.update(
            {
                "title": "Playlist: " + playlist_name,
                "playlist_info": playlist_info,
                "playlist_name": playlist_name,
                "channel_info": channel_info,
                "reindex": reindex.get("state"),
            }
        )
        return render(request, "home/playlist_id.html", self.context)

    def _get_info(self, playlist_id):
        """return additional metadata"""
        # playlist details
        es_path = f"ta_playlist/_doc/{playlist_id}"
        playlist_info = self.single_lookup(es_path)
        channel_info = None
        if playlist_info["playlist_type"] != "custom":
            # channel details
            channel_id = playlist_info["playlist_channel_id"]
            es_path = f"ta_channel/_doc/{channel_id}"
            channel_info = self.single_lookup(es_path)
        return playlist_info, channel_info

    def _update_view_data(self, playlist_id, playlist_info):
        """update view specific data dict"""
        sort = {
            i["youtube_id"]: i["idx"]
            for i in playlist_info["playlist_entries"]
        }
        script = (
            "if(params.scores.containsKey(doc['youtube_id'].value)) "
            + "{return params.scores[doc['youtube_id'].value];} "
            + "return 100000;"
        )
        self.data.update(
            {
                "query": {
                    "bool": {
                        "must": [{"match": {"playlist.keyword": playlist_id}}]
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
        )
        if self.context["hide_watched"]:
            to_append = {"term": {"player.watched": {"value": False}}}
            self.data["query"]["bool"]["must"].append(to_append)


class PlaylistView(ArchivistResultsView):
    """resolves to /playlist/
    show all playlists indexed
    """

    view_origin = "playlist"
    es_search = "ta_playlist/_search"

    def get(self, request):
        """handle get request"""
        self.initiate_vars(request)
        self._update_view_data()
        self.find_results()
        self.context.update(
            {
                "title": "Playlists",
                "subscribe_form": SubscribeToPlaylistForm(),
                "create_form": CreatePlaylistForm(),
            }
        )

        return render(request, "home/playlist.html", self.context)

    def _update_view_data(self):
        """update view specific data dict"""
        self.data["sort"] = [{"playlist_name.keyword": {"order": "asc"}}]
        if self.context["show_subed_only"]:
            self.data["query"] = {
                "term": {"playlist_subscribed": {"value": True}}
            }
        if self.search_get:
            self.data["query"] = {
                "bool": {
                    "should": [
                        {
                            "multi_match": {
                                "query": self.search_get,
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

    @method_decorator(user_passes_test(check_admin), name="dispatch")
    @staticmethod
    def post(request):
        """handle post from subscribe or create form"""
        if request.POST.get("create") is not None:
            create_form = CreatePlaylistForm(data=request.POST)
            if create_form.is_valid():
                name = request.POST.get("create")
                playlist_id = f"TA_playlist_{uuid.uuid4()}"
                YoutubePlaylist(playlist_id).create(name)
        else:
            subscribe_form = SubscribeToPlaylistForm(data=request.POST)
            if subscribe_form.is_valid():
                url_str = request.POST.get("subscribe")
                print(url_str)
                subscribe_to.delay(url_str, expected_type="playlist")

        sleep(1)
        return redirect("playlist")


class VideoView(MinView):
    """resolves to /video/<video-id>/
    display details about a single video
    """

    def get(self, request, video_id):
        """get single video"""
        config_handler = AppConfig()
        response, _ = ElasticWrap(f"ta_video/_doc/{video_id}").get()
        video_data = SearchProcess(response).process()
        if not video_data:
            raise Http404

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

        reindex = ReindexProgress(
            request_type="video", request_id=video_id
        ).get_progress()

        context = self.get_min_context(request)
        context.update(
            {
                "video": video_data,
                "playlist_nav": playlist_nav,
                "title": video_data.get("title"),
                "cast": EnvironmentSettings.ENABLE_CAST,
                "config": config_handler.config,
                "position": time_parser(request.GET.get("t")),
                "reindex": reindex.get("state"),
            }
        )
        return render(request, "home/video.html", context)

    @staticmethod
    def build_playlists(video_id, playlists):
        """build playlist nav if available"""
        all_navs = []
        for playlist_id in playlists:
            playlist = YoutubePlaylist(playlist_id)
            playlist.get_from_es()
            playlist.build_nav(video_id)
            if playlist.nav:
                all_navs.append(playlist.nav)

        return all_navs

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


class SearchView(ArchivistResultsView):
    """resolves to /search/
    handle cross index search interface
    """

    view_origin = "home"
    es_search = ""

    def get(self, request):
        """handle get request"""
        self.initiate_vars(request)
        all_styles = self.get_all_view_styles()
        self.context.update({"all_styles": all_styles})
        self.context.update(
            {
                "search_form": MultiSearchForm(initial=all_styles),
                "version": settings.TA_VERSION,
            }
        )

        return render(request, "home/search.html", self.context)


class SettingsView(MinView):
    """resolves to /settings/
    handle the settings dashboard
    """

    def get(self, request):
        """read and display the dashboard"""
        context = self.get_min_context(request)
        context.update({"title": "Settings Dashboard"})

        return render(request, "home/settings.html", context)


class SettingsUserView(MinView):
    """resolves to /settings/user/
    handle the settings sub-page for user settings,
    display current settings,
    take post request from the form to update settings
    """

    def get(self, request):
        """read and display current settings"""
        context = self.get_min_context(request)
        context.update(
            {
                "title": "User Settings",
                "page_size": UserConfig(request.user.id).get_value(
                    "page_size"
                ),
                "user_form": UserSettingsForm(),
            }
        )

        return render(request, "home/settings_user.html", context)

    def post(self, request):
        """handle form post to update settings"""
        user_form = UserSettingsForm(request.POST)
        config_handler = UserConfig(request.user.id)
        if user_form.is_valid():
            user_form_post = user_form.cleaned_data
            if user_form_post.get("stylesheet"):
                config_handler.set_value(
                    "stylesheet", user_form_post.get("stylesheet")
                )
            if user_form_post.get("page_size"):
                config_handler.set_value(
                    "page_size", user_form_post.get("page_size")
                )

        sleep(1)
        return redirect("settings_user", permanent=True)


@method_decorator(user_passes_test(check_admin), name="dispatch")
class SettingsApplicationView(MinView):
    """resolves to /settings/application/
    handle the settings sub-page for application configuration,
    display current settings,
    take post request from the form to update settings
    """

    def get(self, request):
        """read and display current application settings"""
        context = self.get_min_context(request)
        context.update(
            {
                "title": "Application Settings",
                "config": AppConfig().config,
                "api_token": self.get_token(request),
                "app_form": ApplicationSettingsForm(),
                "snapshots": ElasticSnapshot().get_snapshot_stats(),
            }
        )

        return render(request, "home/settings_application.html", context)

    @staticmethod
    def get_token(request):
        """get existing or create new token of user"""
        # pylint: disable=no-member
        token = Token.objects.get_or_create(user=request.user)[0]
        return token

    def post(self, request):
        """handle form post to update settings"""
        config_handler = AppConfig()

        app_form = ApplicationSettingsForm(request.POST)
        if app_form.is_valid():
            app_form_post = app_form.cleaned_data
            if app_form_post:
                print(app_form_post)
                updated = config_handler.update_config(app_form_post)
                self.post_process_updated(updated, config_handler.config)

        sleep(1)
        return redirect("settings_application", permanent=True)

    def post_process_updated(self, updated, config):
        """apply changes for config"""
        if not updated:
            return

        for config_value, updated_value in updated:
            if config_value == "cookie_import":
                self.process_cookie(config, updated_value)
            if config_value == "enable_snapshot":
                ElasticSnapshot().setup()

    def process_cookie(self, config, updated_value):
        """import and validate cookie"""
        handler = CookieHandler(config)
        if updated_value:
            try:
                handler.import_cookie()
            except FileNotFoundError:
                print("cookie: import failed, file not found")
                handler.revoke()
                self._fail_message("Cookie file not found.")
                return

            valid = handler.validate()
            if not valid:
                handler.revoke()
                self._fail_message("Failed to validate cookie file.")
        else:
            handler.revoke()

    @staticmethod
    def _fail_message(message_line):
        """notify our failure"""
        key = "message:setting"
        message = {
            "status": key,
            "group": "setting:application",
            "level": "error",
            "title": "Cookie import failed",
            "messages": [message_line],
            "id": "0000",
        }
        RedisArchivist().set_message(key, message=message, expire=True)


@method_decorator(user_passes_test(check_admin), name="dispatch")
class SettingsSchedulingView(MinView):
    """resolves to /settings/scheduling/
    handle the settings sub-page for scheduling settings,
    display current settings,
    take post request from the form to update settings
    """

    def get(self, request):
        """read and display current settings"""
        context = self.get_context(request, SchedulerSettingsForm())

        return render(request, "home/settings_scheduling.html", context)

    def post(self, request):
        """handle form post to update settings"""
        scheduler_form = SchedulerSettingsForm(request.POST)
        notification_form = NotificationSettingsForm(request.POST)

        if notification_form.is_valid():
            notification_form_post = notification_form.cleaned_data
            print(notification_form_post)
            if any(notification_form_post.values()):
                task_name = notification_form_post.get("task")
                url = notification_form_post.get("notification_url")
                Notifications(task_name).add_url(url)

        if scheduler_form.is_valid():
            scheduler_form_post = scheduler_form.cleaned_data
            if any(scheduler_form_post.values()):
                print(scheduler_form_post)
                ScheduleBuilder().update_schedule_conf(scheduler_form_post)
        else:
            self.fail_message()
            context = self.get_context(request, scheduler_form)
            return render(request, "home/settings_scheduling.html", context)

        sleep(1)
        return redirect("settings_scheduling", permanent=True)

    def get_context(self, request, scheduler_form):
        """get context"""
        context = self.get_min_context(request)
        all_tasks = CustomPeriodicTask.objects.all()
        context.update(
            {
                "title": "Scheduling Settings",
                "scheduler_form": scheduler_form,
                "notification_form": NotificationSettingsForm(),
                "notifications": get_all_notifications(),
            }
        )
        for task in all_tasks:
            context.update({task.name: task})

        return context

    @staticmethod
    def fail_message():
        """send failure message"""
        mess_dict = {
            "group": "setting:schedule",
            "level": "error",
            "title": "Scheduler update failed.",
            "messages": ["Invalid schedule input"],
            "id": "0000",
        }
        RedisArchivist().set_message("message:setting", mess_dict, expire=True)


@method_decorator(user_passes_test(check_admin), name="dispatch")
class SettingsActionsView(MinView):
    """resolves to /settings/actions/
    handle the settings actions sub-page
    """

    def get(self, request):
        """read and display current settings"""
        context = self.get_min_context(request)
        context.update(
            {
                "title": "Actions",
                "available_backups": ElasticBackup().get_all_backup_files(),
            }
        )

        return render(request, "home/settings_actions.html", context)
