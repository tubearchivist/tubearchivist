"""all API views"""

from api.src.search_processor import SearchProcess
from home.src.download.queue import PendingInteract
from home.src.es.connect import ElasticWrap
from home.src.index.video import SponsorBlock
from home.src.ta.config import AppConfig
from home.src.ta.helper import UrlListParser
from home.src.ta.ta_redis import RedisArchivist, RedisQueue
from home.tasks import extrac_dl, subscribe_to
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

    def __init__(self):
        super().__init__()
        self.response = {"data": False, "config": AppConfig().config}
        self.status_code = False
        self.context = False

    def get_document(self, document_id):
        """get single document from es"""
        path = f"{self.search_base}{document_id}"
        print(path)
        response, status_code = ElasticWrap(path).get()
        try:
            self.response["data"] = SearchProcess(response).process()
        except KeyError:
            print(f"item not found: {document_id}")
            self.response["data"] = False
        self.status_code = status_code

    def get_paginate(self):
        """add pagination detail to response"""
        self.response["paginate"] = False

    def get_document_list(self, data):
        """get a list of results"""
        print(self.search_base)
        response, status_code = ElasticWrap(self.search_base).get(data=data)
        self.response["data"] = SearchProcess(response).process()
        if self.response["data"]:
            self.status_code = status_code
        else:
            self.status_code = 404


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
        # pylint: disable=unused-argument
        """get request"""
        data = {"query": {"match_all": {}}}
        self.get_document_list(data)
        self.get_paginate()

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
        RedisArchivist().set_message(key, message, expire=False)
        self.response = request.data

        return Response(self.response)

    def delete(self, request, video_id):
        """delete progress position"""
        key = f"{request.user.id}:progress:{video_id}"
        RedisArchivist().del_message(key)
        self.response = {"progress-reset": video_id}

        return Response(self.response)


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
        # pylint: disable=unused-argument
        """get request"""
        data = {"query": {"match_all": {}}}
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


class ChannelApiVideoView(ApiBaseView):
    """resolves to /api/channel/<channel-id>/video
    GET: returns a list of videos of channel
    """

    search_base = "ta_video/_search/"

    def get(self, request, channel_id):
        # pylint: disable=unused-argument
        """handle get request"""
        data = {
            "query": {"term": {"channel.channel_id": {"value": channel_id}}}
        }
        self.get_document_list(data)
        self.get_paginate()

        return Response(self.response, status=self.status_code)


class PlaylistApiListView(ApiBaseView):
    """resolves to /api/playlist/
    GET: returns list of indexed playlists
    """

    search_base = "ta_playlist/_search/"

    def get(self, request):
        # pylint: disable=unused-argument
        """handle get request"""
        data = {"query": {"match_all": {}}}
        self.get_document_list(data)
        self.get_paginate()
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
        # pylint: disable=unused-argument
        """handle get request"""
        data = {
            "query": {"term": {"playlist.keyword": {"value": playlist_id}}}
        }
        self.get_document_list(data)
        self.get_paginate()
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
        RedisQueue().clear_item(video_id)

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
        # pylint: disable=unused-argument
        """get request"""
        query_filter = request.GET.get("filter", False)
        data = {
            "query": {"match_all": {}},
            "sort": [{"timestamp": {"order": "asc"}}],
        }
        if query_filter:
            if query_filter not in self.valid_filter:
                message = f"invalid url query filder: {query_filter}"
                print(message)
                return Response({"message": message}, status=400)

            data["query"] = {"term": {"status": {"value": query_filter}}}

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
