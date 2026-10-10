"""base classes to inherit from"""

import re

from common.src.env_settings import EnvironmentSettings
from common.src.es_connect import ElasticWrap
from common.src.index_generic import Pagination
from common.src.search_processor import SearchProcess, process_aggs
from rest_framework import permissions
from rest_framework.authentication import (
    SessionAuthentication,
    TokenAuthentication,
)
from rest_framework.views import APIView


def check_admin(user):
    """check for admin permission for restricted views"""
    return user.is_staff or user.groups.filter(name="admin").exists()


class AdminOnly(permissions.BasePermission):
    """allow only admin"""

    def has_permission(self, request, view):
        return check_admin(request.user)


class AdminWriteOnly(permissions.BasePermission):
    """allow only admin writes"""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return permissions.IsAuthenticated().has_permission(request, view)

        return check_admin(request.user)


class ApiBaseView(APIView):
    """base view to inherit from"""

    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    search_base = ""
    data = ""

    def __init__(self):
        super().__init__()
        self.response = {}
        self.data = {"query": {"match_all": {}}}
        self.status_code = False
        self.context = False
        self.pagination_handler = False

    def get_document(self, document_id, progress_match=None):
        """get single document from es"""
        path = f"{self.search_base}{document_id}"
        response, status_code = ElasticWrap(path).get()
        try:
            self.response = SearchProcess(
                response, match_video_user_progress=progress_match
            ).process()
        except KeyError:
            print(f"item not found: {document_id}")

        self.status_code = status_code

    def initiate_pagination(self, request):
        """set initial pagination values"""
        self.pagination_handler = Pagination(request)
        self.data.update(
            {
                "size": self.pagination_handler.pagination["page_size"],
                "from": self.pagination_handler.pagination["page_from"],
            }
        )

    def get_document_list(self, request, pagination=True, progress_match=None):
        """get a list of results"""
        if pagination:
            self.initiate_pagination(request)

        es_handler = ElasticWrap(self.search_base)
        response, status_code = es_handler.get(data=self.data)
        self.response["data"] = SearchProcess(
            response, match_video_user_progress=progress_match
        ).process()
        if self.response["data"]:
            self.status_code = status_code
        else:
            self.status_code = 404

        if pagination and response.get("hits"):
            self.pagination_handler.validate(
                response["hits"]["total"]["value"]
            )
            self.response["paginate"] = self.pagination_handler.pagination

    def get_aggs(self):
        """get aggs alone"""
        self.data["size"] = 0
        response, _ = ElasticWrap(self.search_base).get(data=self.data)
        process_aggs(response)

        self.response = response.get("aggregations")


class StaticAuthBaseView(APIView):
    """baseview for static files, handle DISABLE_STATIC_AUTH"""

    http_method_names = [method.lower() for method in permissions.SAFE_METHODS]
    permission_classes = (
        [permissions.AllowAny]
        if EnvironmentSettings.DISABLE_STATIC_AUTH
        else [permissions.IsAuthenticated]
    )
    authentication_classes = (
        []
        if EnvironmentSettings.DISABLE_STATIC_AUTH
        else [SessionAuthentication, TokenAuthentication]
    )

    CACHE_CONTROL = (
        "public, max-age=3600"
        if EnvironmentSettings.DISABLE_STATIC_AUTH
        else "private, max-age=3600"
    )

    CHANNEL_ID_REG = re.compile(r"UC[A-Za-z0-9_-]{22}")
    CHANNEL_ART_REG = re.compile(r"banner|thumb|tvart")
    VIDEO_ID_REG = re.compile(r"[A-Za-z0-9_-]{11}")
    PLAYLIST_ID_REG = re.compile(r"(?:LL|WL|[A-Za-z0-9_-]{13,48})")
    SUBTITLE_LANG_REG = re.compile(r"[A-Za-z0-9_-]{2,10}")

    def validate_channel_id(self, channel_id: str) -> None:
        """validate channel id"""
        if not self.CHANNEL_ID_REG.fullmatch(channel_id):
            raise ValueError("invalid channel ID")

    def validate_channel_art_type(self, channel_art: str) -> None:
        """validate channel art type"""
        if not self.CHANNEL_ART_REG.fullmatch(channel_art):
            raise ValueError("invalid channel art type")

    def validate_video_id(self, video_id: str) -> None:
        """validate video id"""
        if not self.VIDEO_ID_REG.fullmatch(video_id):
            raise ValueError("invalid video ID")

    def validate_playlist_id(self, playlist_id: str) -> None:
        """validate playlist id"""
        if not self.PLAYLIST_ID_REG.fullmatch(playlist_id):
            raise ValueError("invalid playlist ID")

    def validate_subtitle_lang(self, lang: str) -> None:
        """validate subtitle lang"""
        if not self.SUBTITLE_LANG_REG.fullmatch(lang):
            raise ValueError("invalid subtitle lang")
