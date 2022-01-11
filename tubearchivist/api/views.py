"""all API views"""

import requests
from home.src.config import AppConfig
from home.src.helper import UrlListParser
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

    def config_builder(self):
        """build confic context"""
        default_conf = AppConfig().config
        self.context = {
            "es_url": default_conf["application"]["es_url"],
            "es_auth": default_conf["application"]["es_auth"],
        }

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
        return Response(self.response, status=self.status_code)


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
