"""all API views"""

from api.src.aggs import (
    BiggestChannel,
    Channel,
    Download,
    DownloadHist,
    Playlist,
    Video,
    WatchProgress,
)
from api.src.search_processor import SearchProcess
from download.src.yt_dlp_base import CookieHandler
from home.src.es.backup import ElasticBackup
from home.src.es.connect import ElasticWrap
from home.src.es.snapshot import ElasticSnapshot
from home.src.frontend.searching import SearchForm
from home.src.frontend.watched import WatchState
from home.src.index.generic import Pagination
from home.src.index.reindex import ReindexProgress
from home.src.ta.config import AppConfig, ReleaseVersion
from home.src.ta.settings import EnvironmentSettings
from home.src.ta.ta_redis import RedisArchivist
from home.src.ta.users import UserConfig
from rest_framework import permissions
from rest_framework.authentication import (
    SessionAuthentication,
    TokenAuthentication,
)
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.response import Response
from rest_framework.views import APIView
from task.src.task_manager import TaskCommand
from task.tasks import check_reindex, run_restore_backup


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


class LoginApiView(ObtainAuthToken):
    """resolves to /api/login/
    POST: return token and username after successful login
    """

    def post(self, request, *args, **kwargs):
        """post data"""
        # pylint: disable=no-member
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, _ = Token.objects.get_or_create(user=user)

        print(f"returning token for user with id {user.pk}")

        return Response(
            {
                "token": token.key,
                "user_id": user.pk,
                "is_superuser": user.is_superuser,
                "is_staff": user.is_staff,
                "user_groups": [group.name for group in user.groups.all()],
            }
        )


class SnapshotApiListView(ApiBaseView):
    """resolves to /api/snapshot/
    GET: returns snapshot config plus list of existing snapshots
    POST: take snapshot now
    """

    permission_classes = [AdminOnly]

    @staticmethod
    def get(request):
        """handle get request"""
        # pylint: disable=unused-argument
        snapshots = ElasticSnapshot().get_snapshot_stats()

        return Response(snapshots)

    @staticmethod
    def post(request):
        """take snapshot now with post request"""
        # pylint: disable=unused-argument
        response = ElasticSnapshot().take_snapshot_now()

        return Response(response)


class SnapshotApiView(ApiBaseView):
    """resolves to /api/snapshot/<snapshot-id>/
    GET: return a single snapshot
    POST: restore snapshot
    DELETE: delete a snapshot
    """

    permission_classes = [AdminOnly]

    @staticmethod
    def get(request, snapshot_id):
        """handle get request"""
        # pylint: disable=unused-argument
        snapshot = ElasticSnapshot().get_single_snapshot(snapshot_id)

        if not snapshot:
            return Response({"message": "snapshot not found"}, status=404)

        return Response(snapshot)

    @staticmethod
    def post(request, snapshot_id):
        """restore snapshot with post request"""
        # pylint: disable=unused-argument
        response = ElasticSnapshot().restore_all(snapshot_id)
        if not response:
            message = {"message": "failed to restore snapshot"}
            return Response(message, status=400)

        return Response(response)

    @staticmethod
    def delete(request, snapshot_id):
        """delete snapshot from index"""
        # pylint: disable=unused-argument
        response = ElasticSnapshot().delete_single_snapshot(snapshot_id)
        if not response:
            message = {"message": "failed to delete snapshot"}
            return Response(message, status=400)

        return Response(response)


class BackupApiListView(ApiBaseView):
    """resolves to /api/backup/
    GET: returns list of available zip backups
    POST: take zip backup now
    """

    permission_classes = [AdminOnly]
    task_name = "run_backup"

    @staticmethod
    def get(request):
        """handle get request"""
        # pylint: disable=unused-argument
        backup_files = ElasticBackup().get_all_backup_files()
        return Response(backup_files)

    def post(self, request):
        """handle post request"""
        # pylint: disable=unused-argument
        response = TaskCommand().start(self.task_name)
        message = {
            "message": "backup task started",
            "task_id": response["task_id"],
        }

        return Response(message)


class BackupApiView(ApiBaseView):
    """resolves to /api/backup/<filename>/
    GET: return a single backup
    POST: restore backup
    DELETE: delete backup
    """

    permission_classes = [AdminOnly]
    task_name = "restore_backup"

    @staticmethod
    def get(request, filename):
        """get single backup"""
        # pylint: disable=unused-argument
        backup_file = ElasticBackup().build_backup_file_data(filename)
        if not backup_file:
            message = {"message": "file not found"}
            return Response(message, status=404)

        return Response(backup_file)

    def post(self, request, filename):
        """restore backup file"""
        # pylint: disable=unused-argument
        task = run_restore_backup.delay(filename)
        message = {
            "message": "backup restore task started",
            "filename": filename,
            "task_id": task.id,
        }
        return Response(message)

    @staticmethod
    def delete(request, filename):
        """delete backup file"""
        # pylint: disable=unused-argument

        backup_file = ElasticBackup().delete_file(filename)
        if not backup_file:
            message = {"message": "file not found"}
            return Response(message, status=404)

        message = {"message": f"file {filename} deleted"}
        return Response(message)


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


class UserConfigView(ApiBaseView):
    """resolves to /api/config/user/
    GET: return current user config
    POST: update user config
    """

    def get(self, request):
        """get config"""
        user_id = request.user.id
        response = UserConfig(user_id).get_config()
        response.update({"user_id": user_id})

        return Response(response)

    def post(self, request):
        """update config"""
        user_id = request.user.id
        data = request.data

        user_conf = UserConfig(user_id)
        for key, value in data.items():
            try:
                user_conf.set_value(key, value)
            except ValueError as err:
                message = {
                    "status": "Bad Request",
                    "message": f"failed updating {key} to '{value}', {err}",
                }
                return Response(message, status=400)

        response = user_conf.get_config()
        response.update({"user_id": user_id})

        return Response(response)


class CookieView(ApiBaseView):
    """resolves to /api/cookie/
    GET: check if cookie is enabled
    POST: verify validity of cookie
    PUT: import cookie
    """

    permission_classes = [AdminOnly]

    @staticmethod
    def get(request):
        """handle get request"""
        # pylint: disable=unused-argument
        config = AppConfig().config
        valid = RedisArchivist().get_message("cookie:valid")
        response = {"cookie_enabled": config["downloads"]["cookie_import"]}
        response.update(valid)

        return Response(response)

    @staticmethod
    def post(request):
        """handle post request"""
        # pylint: disable=unused-argument
        config = AppConfig().config
        validated = CookieHandler(config).validate()

        return Response({"cookie_validated": validated})

    @staticmethod
    def put(request):
        """handle put request"""
        # pylint: disable=unused-argument
        config = AppConfig().config
        cookie = request.data.get("cookie")
        if not cookie:
            message = "missing cookie key in request data"
            print(message)
            return Response({"message": message}, status=400)

        print(f"cookie preview:\n\n{cookie[:300]}")
        handler = CookieHandler(config)
        handler.set_cookie(cookie)
        validated = handler.validate()
        if not validated:
            handler.revoke()
            message = {"cookie_import": "fail", "cookie_validated": validated}
            print(f"cookie: {message}")
            return Response({"message": message}, status=400)

        message = {"cookie_import": "done", "cookie_validated": validated}
        return Response(message)


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


class TokenView(ApiBaseView):
    """resolves to /api/token/
    DELETE: revoke the token
    """

    permission_classes = [AdminOnly]

    @staticmethod
    def delete(request):
        print("revoke API token")
        request.user.auth_token.delete()
        return Response({"success": True})


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


class StatVideoView(ApiBaseView):
    """resolves to /api/stats/video/
    GET: return video stats
    """

    def get(self, request):
        """get stats"""
        # pylint: disable=unused-argument

        return Response(Video().process())


class StatChannelView(ApiBaseView):
    """resolves to /api/stats/channel/
    GET: return channel stats
    """

    def get(self, request):
        """get stats"""
        # pylint: disable=unused-argument

        return Response(Channel().process())


class StatPlaylistView(ApiBaseView):
    """resolves to /api/stats/playlist/
    GET: return playlist stats
    """

    def get(self, request):
        """get stats"""
        # pylint: disable=unused-argument

        return Response(Playlist().process())


class StatDownloadView(ApiBaseView):
    """resolves to /api/stats/download/
    GET: return download stats
    """

    def get(self, request):
        """get stats"""
        # pylint: disable=unused-argument

        return Response(Download().process())


class StatWatchProgress(ApiBaseView):
    """resolves to /api/stats/watchprogress/
    GET: return watch/unwatch progress stats
    """

    def get(self, request):
        """handle get request"""
        # pylint: disable=unused-argument

        return Response(WatchProgress().process())


class StatDownloadHist(ApiBaseView):
    """resolves to /api/stats/downloadhist/
    GET: return download video count histogram for last days
    """

    def get(self, request):
        """handle get request"""
        # pylint: disable=unused-argument

        return Response(DownloadHist().process())


class StatBiggestChannel(ApiBaseView):
    """resolves to /api/stats/biggestchannels/
    GET: return biggest channels
    param: order
    """

    order_choices = ["doc_count", "duration", "media_size"]

    def get(self, request):
        """handle get request"""

        order = request.GET.get("order", "doc_count")
        if order and order not in self.order_choices:
            message = {"message": f"invalid order parameter {order}"}
            return Response(message, status=400)

        return Response(BiggestChannel(order).process())
