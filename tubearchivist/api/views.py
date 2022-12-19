"""all API views"""

from api.src.search_processor import SearchProcess
from api.src.task_processor import TaskHandler
from home.src.download.queue import PendingInteract
from home.src.download.yt_dlp_base import CookieHandler
from home.src.es.connect import ElasticWrap
from home.src.es.snapshot import ElasticSnapshot
from home.src.frontend.searching import SearchForm
from home.src.index.generic import Pagination
from home.src.index.reindex import ReindexProgress
from home.src.index.video import SponsorBlock
from home.src.ta.config import AppConfig
from home.src.ta.helper import UrlListParser
from home.src.ta.ta_redis import RedisArchivist, RedisQueue
from home.tasks import check_reindex, extrac_dl, subscribe_to
from rest_framework.authentication import (
    SessionAuthentication,
    TokenAuthentication,
)
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class ApiBaseView(APIView):
    """base view to inherit from"""

    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    search_base = False
    data = False

    def __init__(self):
        super().__init__()
        self.response = {"data": False, "config": AppConfig().config}
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


class VideoApiView(ApiBaseView):
    """resolves to /api/video/<video_id>/
    GET: returns metadata dict of video
    """

    search_base = "ta_video/_doc/"

    def get(self, request, video_id):
        # pylint: disable=unused-argument
        """get request"""
        self.get_document(video_id)
        return Response(self.response, status=self.status_code)


class VideoApiListView(ApiBaseView):
    """resolves to /api/video/
    GET: returns list of videos
    """

    search_base = "ta_video/_search/"

    def get(self, request):
        """get request"""
        self.data.update({"sort": [{"published": {"order": "desc"}}]})
        self.get_document_list(request)

        return Response(self.response)


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
        message = {"position": position, "youtube_id": video_id}
        RedisArchivist().set_message(key, message)
        self.response = request.data

        return Response(self.response)

    def delete(self, request, video_id):
        """delete progress position"""
        key = f"{request.user.id}:progress:{video_id}"
        RedisArchivist().del_message(key)
        self.response = {"progress-reset": video_id}

        return Response(self.response)


class VideoCommentView(ApiBaseView):
    """resolves to /api/video/<video_id>/comment/
    handle video comments
    GET: return all comments from video with reply threads
    """

    search_base = "ta_comment/_doc/"

    def get(self, request, video_id):
        """get video comments"""
        # pylint: disable=unused-argument
        self.get_document(video_id)

        return Response(self.response, status=self.status_code)


class VideoSimilarView(ApiBaseView):
    """resolves to /api/video/<video-id>/similar/
    GET: return max 3 videos similar to this
    """

    search_base = "ta_video/_search/"

    def get(self, request, video_id):
        """get similar videos"""
        self.data = {
            "size": 6,
            "query": {
                "more_like_this": {
                    "fields": ["tags", "title"],
                    "like": {"_id": video_id},
                    "min_term_freq": 1,
                    "max_query_terms": 25,
                }
            },
        }
        self.get_document_list(request, pagination=False)
        return Response(self.response, status=self.status_code)


class VideoSponsorView(ApiBaseView):
    """resolves to /api/video/<video_id>/sponsor/
    handle sponsor block integration
    """

    search_base = "ta_video/_doc/"

    def get(self, request, video_id):
        """get sponsor info"""
        # pylint: disable=unused-argument

        self.get_document(video_id)
        sponsorblock = self.response["data"].get("sponsorblock")

        return Response(sponsorblock)

    def post(self, request, video_id):
        """post verification and timestamps"""
        if "segment" in request.data:
            response, status_code = self._create_segment(request, video_id)
        elif "vote" in request.data:
            response, status_code = self._vote_on_segment(request)

        return Response(response, status=status_code)

    @staticmethod
    def _create_segment(request, video_id):
        """create segment in API"""
        start_time = request.data["segment"]["startTime"]
        end_time = request.data["segment"]["endTime"]
        response, status_code = SponsorBlock(request.user.id).post_timestamps(
            video_id, start_time, end_time
        )

        return response, status_code

    @staticmethod
    def _vote_on_segment(request):
        """validate on existing segment"""
        user_id = request.user.id
        uuid = request.data["vote"]["uuid"]
        vote = request.data["vote"]["yourVote"]
        response, status_code = SponsorBlock(user_id).vote_on_segment(
            uuid, vote
        )

        return response, status_code


class ChannelApiView(ApiBaseView):
    """resolves to /api/channel/<channel_id>/
    GET: returns metadata dict of channel
    """

    search_base = "ta_channel/_doc/"

    def get(self, request, channel_id):
        # pylint: disable=unused-argument
        """get request"""
        self.get_document(channel_id)
        return Response(self.response, status=self.status_code)


class ChannelApiListView(ApiBaseView):
    """resolves to /api/channel/
    GET: returns list of channels
    POST: edit a list of channels
    """

    search_base = "ta_channel/_search/"

    def get(self, request):
        """get request"""
        self.get_document_list(request)
        self.data.update(
            {"sort": [{"channel_name.keyword": {"order": "asc"}}]}
        )

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


class ChannelApiVideoView(ApiBaseView):
    """resolves to /api/channel/<channel-id>/video
    GET: returns a list of videos of channel
    """

    search_base = "ta_video/_search/"

    def get(self, request, channel_id):
        """handle get request"""
        self.data.update(
            {
                "query": {
                    "term": {"channel.channel_id": {"value": channel_id}}
                },
                "sort": [{"published": {"order": "desc"}}],
            }
        )
        self.get_document_list(request)

        return Response(self.response, status=self.status_code)


class PlaylistApiListView(ApiBaseView):
    """resolves to /api/playlist/
    GET: returns list of indexed playlists
    """

    search_base = "ta_playlist/_search/"

    def get(self, request):
        """handle get request"""
        self.data.update(
            {"sort": [{"playlist_name.keyword": {"order": "asc"}}]}
        )
        self.get_document_list(request)
        return Response(self.response)


class PlaylistApiView(ApiBaseView):
    """resolves to /api/playlist/<playlist_id>/
    GET: returns metadata dict of playlist
    """

    search_base = "ta_playlist/_doc/"

    def get(self, request, playlist_id):
        # pylint: disable=unused-argument
        """get request"""
        self.get_document(playlist_id)
        return Response(self.response, status=self.status_code)


class PlaylistApiVideoView(ApiBaseView):
    """resolves to /api/playlist/<playlist_id>/video
    GET: returns list of videos in playlist
    """

    search_base = "ta_video/_search/"

    def get(self, request, playlist_id):
        """handle get request"""
        self.data["query"] = {
            "term": {"playlist.keyword": {"value": playlist_id}}
        }
        self.data.update({"sort": [{"published": {"order": "desc"}}]})

        self.get_document_list(request)
        return Response(self.response, status=self.status_code)


class DownloadApiView(ApiBaseView):
    """resolves to /api/download/<video_id>/
    GET: returns metadata dict of an item in the download queue
    POST: update status of item to pending or ignore
    DELETE: forget from download queue
    """

    search_base = "ta_download/_doc/"
    valid_status = ["pending", "ignore"]

    def get(self, request, video_id):
        # pylint: disable=unused-argument
        """get request"""
        self.get_document(video_id)
        return Response(self.response, status=self.status_code)

    def post(self, request, video_id):
        """post to video to change status"""
        item_status = request.data["status"]
        if item_status not in self.valid_status:
            message = f"{video_id}: invalid status {item_status}"
            print(message)
            return Response({"message": message}, status=400)

        print(f"{video_id}: change status to {item_status}")
        PendingInteract(video_id=video_id, status=item_status).update_status()
        RedisQueue(queue_name="dl_queue").clear_item(video_id)

        return Response(request.data)

    @staticmethod
    def delete(request, video_id):
        # pylint: disable=unused-argument
        """delete single video from queue"""
        print(f"{video_id}: delete from queue")
        PendingInteract(video_id=video_id).delete_item()

        return Response({"success": True})


class DownloadApiListView(ApiBaseView):
    """resolves to /api/download/
    GET: returns latest videos in the download queue
    POST: add a list of videos to download queue
    DELETE: remove items based on query filter
    """

    search_base = "ta_download/_search/"
    valid_filter = ["pending", "ignore"]

    def get(self, request):
        """get request"""
        query_filter = request.GET.get("filter", False)
        self.data.update({"sort": [{"timestamp": {"order": "asc"}}]})

        must_list = []
        if query_filter:
            if query_filter not in self.valid_filter:
                message = f"invalid url query filder: {query_filter}"
                print(message)
                return Response({"message": message}, status=400)

            must_list.append({"term": {"status": {"value": query_filter}}})

        filter_channel = request.GET.get("channel", False)
        if filter_channel:
            must_list.append(
                {"term": {"channel_id": {"value": filter_channel}}}
            )

        self.data["query"] = {"bool": {"must": must_list}}

        self.get_document_list(request)
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

    def delete(self, request):
        """delete download queue"""
        query_filter = request.GET.get("filter", False)
        if query_filter not in self.valid_filter:
            message = f"invalid url query filter: {query_filter}"
            print(message)
            return Response({"message": message}, status=400)

        message = f"delete queue by status: {query_filter}"
        print(message)
        PendingInteract(status=query_filter).delete_by_status()

        return Response({"message": message})


class PingView(ApiBaseView):
    """resolves to /api/ping/
    GET: test your connection
    """

    @staticmethod
    def get(request):
        """get pong"""
        data = {"response": "pong", "user": request.user.id}
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

        return Response({"token": token.key, "user_id": user.pk})


class TaskApiView(ApiBaseView):
    """resolves to /api/task/
    GET: check if ongoing background task
    POST: start a new background task
    """

    @staticmethod
    def get(request):
        """handle get request"""
        # pylint: disable=unused-argument
        response = {"rescan": False, "downloading": False}
        for key in response.keys():
            response[key] = RedisArchivist().is_locked(key)

        return Response(response)

    def post(self, request):
        """handle post request"""
        response = TaskHandler(request.data).run_task()

        return Response(response)


class SnapshotApiListView(ApiBaseView):
    """resolves to /api/snapshot/
    GET: returns snashot config plus list of existing snapshots
    POST: take snapshot now
    """

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


class RefreshView(ApiBaseView):
    """resolves to /api/refresh/
    GET: get refresh progress
    POST: start a manual refresh task
    """

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


class CookieView(ApiBaseView):
    """resolves to /api/cookie/
    GET: check if cookie is enabled
    POST: verify validity of cookie
    PUT: import cookie
    """

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
