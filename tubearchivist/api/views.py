"""all API views"""

import requests
from home.src.config import AppConfig
from rest_framework.response import Response
from rest_framework.views import APIView


class ApiBaseView(APIView):
    """base view to inherit from"""

    search_base = False

    def __init__(self):
        super().__init__()
        self.response = False
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
        self.response = response.json()["_source"]
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
        return Response(self.response)


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
        return Response(self.response)


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
        return Response(self.response)
