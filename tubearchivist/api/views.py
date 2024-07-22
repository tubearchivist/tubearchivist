"""all API views"""

from api.src.search_processor import SearchProcess
from appsettings.src.reindex import ReindexProgress
from home.src.es.connect import ElasticWrap
from home.src.frontend.searching import SearchForm
from home.src.frontend.watched import WatchState
from home.src.index.generic import Pagination
from home.src.ta.config import AppConfig, ReleaseVersion
from home.src.ta.settings import EnvironmentSettings
from home.src.ta.ta_redis import RedisArchivist
from rest_framework import permissions
from rest_framework.authentication import (
    SessionAuthentication,
    TokenAuthentication,
)
from rest_framework.response import Response
from rest_framework.views import APIView
from task.tasks import check_reindex


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

    def get_document(self, document_id):
        """get single document from es"""
        path = f"{self.search_base}{document_id}"
        response, status_code = ElasticWrap(path).get()
        try:
            self.response["data"] = SearchProcess(response).process()
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

    def get_document_list(self, request, pagination=True):
        """get a list of results"""
        if pagination:
            self.initiate_pagination(request)

        es_handler = ElasticWrap(self.search_base)
        response, status_code = es_handler.get(data=self.data)
        self.response["data"] = SearchProcess(response).process()
        if self.response["data"]:
            self.status_code = status_code
        else:
            self.status_code = 404

        if pagination:
            self.pagination_handler.validate(
                response["hits"]["total"]["value"]
            )
            self.response["paginate"] = self.pagination_handler.pagination


class PingView(ApiBaseView):
    """resolves to /api/ping/
    GET: test your connection
    """

    @staticmethod
    def get(request):
        """get pong"""
        data = {
            "response": "pong",
            "user": request.user.id,
            "version": ReleaseVersion().get_local_version(),
        }
        return Response(data)


class RefreshView(ApiBaseView):
    """resolves to /api/refresh/
    GET: get refresh progress
    POST: start a manual refresh task
    """

    permission_classes = [AdminOnly]

    def get(self, request):
        """handle get request"""
        request_type = request.GET.get("type")
        request_id = request.GET.get("id")

        if request_id and not request_type:
            return Response({"status": "Bad Request"}, status=400)

        try:
            progress = ReindexProgress(
                request_type=request_type, request_id=request_id
            ).get_progress()
        except ValueError:
            return Response({"status": "Bad Request"}, status=400)

        return Response(progress)

    def post(self, request):
        """handle post request"""
        data = request.data
        extract_videos = bool(request.GET.get("extract_videos", False))
        check_reindex.delay(data=data, extract_videos=extract_videos)

        return Response(data)


class WatchedView(ApiBaseView):
    """resolves to /api/watched/
    POST: change watched state of video, channel or playlist
    """

    def post(self, request):
        """change watched state"""
        youtube_id = request.data.get("id")
        is_watched = request.data.get("is_watched")

        if not youtube_id or is_watched is None:
            message = {"message": "missing id or is_watched"}
            return Response(message, status=400)

        WatchState(youtube_id, is_watched).change()
        return Response({"message": "success"}, status=200)


class SearchView(ApiBaseView):
    """resolves to /api/search/
    GET: run a search with the string in the ?query parameter
    """

    @staticmethod
    def get(request):
        """handle get request
        search through all indexes"""
        search_query = request.GET.get("query", None)
        if search_query is None:
            return Response(
                {"message": "no search query specified"}, status=400
            )

        search_results = SearchForm().multi_search(search_query)
        return Response(search_results)


class NotificationView(ApiBaseView):
    """resolves to /api/notification/
    GET: returns a list of notifications
    filter query to filter messages by group
    """

    valid_filters = ["download", "settings", "channel"]

    def get(self, request):
        """get all notifications"""
        query = "message"
        filter_by = request.GET.get("filter", None)
        if filter_by in self.valid_filters:
            query = f"{query}:{filter_by}"

        return Response(RedisArchivist().list_items(query))
