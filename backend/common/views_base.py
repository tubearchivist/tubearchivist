"""base classes to inherit from"""

from appsettings.src.config import AppConfig
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
        self.response = {
            "data": False,
            "config": {
                "enable_cast": EnvironmentSettings.ENABLE_CAST,
                "downloads": AppConfig().config["downloads"],
            },
        }
        self.data = {"query": {"match_all": {}}}
        self.status_code = False
        self.context = False
        self.pagination_handler = False

    def get_document(self, document_id, progress_match=None):
        """get single document from es"""
        path = f"{self.search_base}{document_id}"
        response, status_code = ElasticWrap(path).get()
        try:
            self.response["data"] = SearchProcess(
                response, match_video_user_progress=progress_match
            ).process()
        except KeyError:
            print(f"item not found: {document_id}")
            self.response["data"] = False
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
