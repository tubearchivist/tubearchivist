"""all API views"""

from appsettings.src.config import ReleaseVersion
from appsettings.src.reindex import ReindexProgress
from common.src.searching import SearchForm
from common.src.ta_redis import RedisArchivist
from common.src.watched import WatchState
from common.views_base import AdminOnly, ApiBaseView
from rest_framework.response import Response
from task.tasks import check_reindex


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
            "ta_update": ReleaseVersion().get_update(),
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

        WatchState(youtube_id, is_watched, request.user.id).change()
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
