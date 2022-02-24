"""all API views"""

import requests
from home.src.download.thumbnails import ThumbManager
from home.src.ta.config import AppConfig
from home.src.ta.helper import UrlListParser
from home.src.ta.ta_redis import RedisArchivist
from home.tasks import extrac_dl, subscribe_to
from rest_framework.authentication import (
    SessionAuthentication,
    TokenAuthentication,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class ApiBaseView(APIView):
    """base view to inherit from"""

    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    search_base = False

    def __init__(self):
        super().__init__()
        self.response = {"data": False}
        self.status_code = False
        self.context = False
        self.default_conf = AppConfig().config

    def config_builder(self):
        """build confic context"""
        self.context = {
            "es_url": self.default_conf["application"]["es_url"],
            "es_auth": self.default_conf["application"]["es_auth"],
        }
        self.response["config"] = self.default_conf

    def get_document(self, document_id):
        """get single document from es"""
        es_url = self.context["es_url"]
        url = f"{es_url}{self.search_base}{document_id}"
        print(url)
        response = requests.get(url, auth=self.context["es_auth"])
        try:
            self.response["data"] = response.json()["_source"]
        except KeyError:
            print(f"item not found: {document_id}")
            self.response["data"] = False
        self.status_code = response.status_code

    def process_keys(self):
        """process keys for frontend"""
        all_keys = self.response["data"].keys()
        if "media_url" in all_keys:
            media_url = self.response["data"]["media_url"]
            self.response["data"]["media_url"] = f"/media/{media_url}"
        if "vid_thumb_url" in all_keys:
            youtube_id = self.response["data"]["youtube_id"]
            vid_thumb_url = ThumbManager().vid_thumb_path(youtube_id)
            cache_dir = self.default_conf["application"]["cache_dir"]
            new_thumb = f"{cache_dir}/{vid_thumb_url}"
            self.response["data"]["vid_thumb_url"] = new_thumb
        if "subtitles" in all_keys:
            all_subtitles = self.response["data"]["subtitles"]
            for idx, _ in enumerate(all_subtitles):
                url = self.response["data"]["subtitles"][idx]["media_url"]
                new_url = f"/media/{url}"
                self.response["data"]["subtitles"][idx]["media_url"] = new_url

    def get_paginate(self):
        """add pagination detail to response"""
        self.response["paginate"] = False

    def get_document_list(self, data):
        """get a list of results"""
        es_url = self.context["es_url"]
        url = f"{es_url}{self.search_base}"
        print(url)
        response = requests.get(url, json=data, auth=self.context["es_auth"])
        all_hits = response.json()["hits"]["hits"]
        self.response["data"] = [i["_source"] for i in all_hits]
        self.status_code = response.status_code


class VideoApiView(ApiBaseView):
    """resolves to /api/video/<video_id>/
    GET: returns metadata dict of video
    """

    search_base = "/ta_video/_doc/"

    def get(self, request, video_id):
        # pylint: disable=unused-argument
        """get request"""
        self.config_builder()
        self.get_document(video_id)
        self.process_keys()
        return Response(self.response, status=self.status_code)


class VideoProgressView(ApiBaseView):
    """resolves to /api/video/<video_id>/
    handle progress status for video
    """

    def get(self, request, video_id):
        """get progress for a single video"""
        user_id = request.user.id
        key = f"{user_id}:progress:{video_id}"
        video_progress = RedisArchivist().get_message(key)
        position = video_progress.get("position", 0)

        self.response = {
            "youtube_id": video_id,
            "user_id": user_id,
            "position": position,
        }
        return Response(self.response)

    def post(self, request, video_id):
        """set progress position in redis"""
        position = request.data.get("position", 0)
        key = f"{request.user.id}:progress:{video_id}"
        message = {"position": position}
        RedisArchivist().set_message(key, message, expire=False)
        self.response = request.data

        return Response(self.response)

    def delete(self, request, video_id):
        """delete progress position"""
        key = f"{request.user.id}:progress:{video_id}"
        RedisArchivist().del_message(key)
        self.response = {"progress-reset": video_id}

        return Response(self.response)


class ChannelApiView(ApiBaseView):
    """resolves to /api/channel/<channel_id>/
    GET: returns metadata dict of channel
    """

    search_base = "/ta_channel/_doc/"

    def get(self, request, channel_id):
        # pylint: disable=unused-argument
        """get request"""
        self.config_builder()
        self.get_document(channel_id)
        return Response(self.response, status=self.status_code)


class ChannelApiListView(ApiBaseView):
    """resolves to /api/channel/
    GET: returns list of channels
    POST: edit a list of channels
    """

    search_base = "/ta_channel/_search/"

    def get(self, request):
        # pylint: disable=unused-argument
        """get request"""
        data = {"query": {"match_all": {}}}
        self.config_builder()
        self.get_document_list(data)
        self.get_paginate()

        return Response(self.response)

    @staticmethod
    def post(request):
        """subscribe to list of channels"""
        data = request.data
        try:
            to_add = data["data"]
        except KeyError:
            message = "missing expected data key"
            print(message)
            return Response({"message": message}, status=400)

        pending = [i["channel_id"] for i in to_add if i["channel_subscribed"]]
        url_str = " ".join(pending)
        subscribe_to.delay(url_str)

        return Response(data)


class PlaylistApiView(ApiBaseView):
    """resolves to /api/playlist/<playlist_id>/
    GET: returns metadata dict of playlist
    """

    search_base = "/ta_playlist/_doc/"

    def get(self, request, playlist_id):
        # pylint: disable=unused-argument
        """get request"""
        self.config_builder()
        self.get_document(playlist_id)
        return Response(self.response, status=self.status_code)


class DownloadApiView(ApiBaseView):
    """resolves to /api/download/<video_id>/
    GET: returns metadata dict of an item in the download queue
    """

    search_base = "/ta_download/_doc/"

    def get(self, request, video_id):
        # pylint: disable=unused-argument
        """get request"""
        self.config_builder()
        self.get_document(video_id)
        return Response(self.response, status=self.status_code)


class DownloadApiListView(ApiBaseView):
    """resolves to /api/download/
    GET: returns latest videos in the download queue
    POST: add a list of videos to download queue
    """

    search_base = "/ta_download/_search/"

    def get(self, request):
        # pylint: disable=unused-argument
        """get request"""
        data = {"query": {"match_all": {}}}
        self.config_builder()
        self.get_document_list(data)
        self.get_paginate()
        return Response(self.response)

    @staticmethod
    def post(request):
        """add list of videos to download queue"""
        print(f"request meta data: {request.META}")
        data = request.data
        try:
            to_add = data["data"]
        except KeyError:
            message = "missing expected data key"
            print(message)
            return Response({"message": message}, status=400)

        pending = [i["youtube_id"] for i in to_add if i["status"] == "pending"]
        url_str = " ".join(pending)
        try:
            youtube_ids = UrlListParser(url_str).process_list()
        except ValueError:
            message = f"failed to parse: {url_str}"
            print(message)
            return Response({"message": message}, status=400)

        extrac_dl.delay(youtube_ids)

        return Response(data)
