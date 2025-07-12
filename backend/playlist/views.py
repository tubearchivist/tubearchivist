"""all playlist API views"""

import uuid

from common.serializers import (
    AsyncTaskResponseSerializer,
    ErrorResponseSerializer,
)
from common.views_base import AdminWriteOnly, ApiBaseView
from drf_spectacular.utils import OpenApiResponse, extend_schema
from playlist.serializers import (
    PlaylistBulkAddSerializer,
    PlaylistCustomPostSerializer,
    PlaylistDeleteQuerySerializer,
    PlaylistListCustomPostSerializer,
    PlaylistListQuerySerializer,
    PlaylistListSerializer,
    PlaylistSerializer,
    PlaylistSingleUpdate,
)
from playlist.src.index import YoutubePlaylist
from playlist.src.query_building import QueryBuilder
from rest_framework.response import Response
from task.tasks import subscribe_to
from user.src.user_config import UserConfig


class PlaylistApiListView(ApiBaseView):
    """resolves to /api/playlist/
    GET: returns list of indexed playlists
    params:
    - channel:str=<channel-id>
    - subscribed: bool
    - type:enum=regular|custom
    POST: change subscribe state
    """

    search_base = "ta_playlist/_search/"
    permission_classes = [AdminWriteOnly]

    @extend_schema(
        responses={
            200: OpenApiResponse(PlaylistListSerializer()),
            400: OpenApiResponse(
                ErrorResponseSerializer(), description="Bad request"
            ),
        },
        parameters=[PlaylistListQuerySerializer],
    )
    def get(self, request):
        """get playlist list"""
        query_serializer = PlaylistListQuerySerializer(
            data=request.query_params
        )
        query_serializer.is_valid(raise_exception=True)
        validated_query = query_serializer.validated_data
        try:
            data = QueryBuilder(**validated_query).build_data()
        except ValueError as err:
            error = ErrorResponseSerializer({"error": str(err)})
            return Response(error.data, status=400)

        self.data = data
        self.get_document_list(request)

        response_serializer = PlaylistListSerializer(self.response)

        return Response(response_serializer.data)

    @extend_schema(
        request=PlaylistBulkAddSerializer(),
        responses={
            200: OpenApiResponse(AsyncTaskResponseSerializer()),
            400: OpenApiResponse(
                ErrorResponseSerializer(), description="Bad request"
            ),
        },
    )
    def post(self, request):
        """async subscribe to list of playlists"""
        data_serializer = PlaylistBulkAddSerializer(data=request.data)
        data_serializer.is_valid(raise_exception=True)
        validated_data = data_serializer.validated_data

        pending = [i["playlist_id"] for i in validated_data["data"]]
        if not pending:
            error = ErrorResponseSerializer({"error": "nothing to subscribe"})
            return Response(error.data, status=400)

        url_str = " ".join(pending)
        task = subscribe_to.delay(url_str, expected_type="playlist")

        message = {
            "message": "playlist subscribe task started",
            "task_id": task.id,
        }
        serializer = AsyncTaskResponseSerializer(message)

        return Response(serializer.data)


class PlaylistCustomApiListView(ApiBaseView):
    """resolves to /api/playlist/custom/
    POST: Create new custom playlist
    """

    search_base = "ta_playlist/_search/"
    permission_classes = [AdminWriteOnly]

    @extend_schema(
        request=PlaylistListCustomPostSerializer(),
        responses={
            200: OpenApiResponse(PlaylistSerializer()),
            400: OpenApiResponse(
                ErrorResponseSerializer(), description="Bad request"
            ),
        },
    )
    def post(self, request):
        """create new custom playlist"""
        serializer = PlaylistListCustomPostSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        custom_name = validated_data["playlist_name"]
        playlist_id = f"TA_playlist_{uuid.uuid4()}"
        custom_playlist = YoutubePlaylist(playlist_id)
        custom_playlist.create(custom_name)

        response_serializer = PlaylistSerializer(custom_playlist.json_data)

        return Response(response_serializer.data)


class PlaylistCustomApiView(ApiBaseView):
    """resolves to /api/playlist/custom/<playlist_id>/
    POST: modify custom playlist
    """

    search_base = "ta_playlist/_doc/"
    permission_classes = [AdminWriteOnly]

    @extend_schema(
        request=PlaylistCustomPostSerializer(),
        responses={
            200: OpenApiResponse(PlaylistSerializer()),
            400: OpenApiResponse(
                ErrorResponseSerializer(), description="bad request"
            ),
            404: OpenApiResponse(
                ErrorResponseSerializer(), description="playlist not found"
            ),
        },
    )
    def post(self, request, playlist_id):
        """modify custom playlist"""
        data_serializer = PlaylistCustomPostSerializer(data=request.data)
        data_serializer.is_valid(raise_exception=True)
        validated_data = data_serializer.validated_data

        self.get_document(playlist_id)
        if not self.response:
            error = ErrorResponseSerializer({"error": "playlist not found"})
            return Response(error.data, status=404)

        if not self.response["playlist_type"] == "custom":
            error = ErrorResponseSerializer(
                {"error": f"playlist with ID {playlist_id} is not custom"}
            )
            return Response(error.data, status=400)

        action = validated_data.get("action")
        video_id = validated_data.get("video_id")

        playlist = YoutubePlaylist(playlist_id)
        if action == "create":
            try:
                playlist.add_video_to_playlist(video_id)
            except TypeError:
                error = ErrorResponseSerializer(
                    {"error": f"failed to add video {video_id} to playlist"}
                )
                return Response(error.data, status=400)
        else:
            hide = UserConfig(request.user.id).get_value("hide_watched")
            playlist.move_video(video_id, action, hide_watched=hide)

        response_serializer = PlaylistSerializer(playlist.json_data)

        return Response(response_serializer.data)


class PlaylistApiView(ApiBaseView):
    """resolves to /api/playlist/<playlist_id>/
    GET: returns metadata dict of playlist
    """

    search_base = "ta_playlist/_doc/"
    permission_classes = [AdminWriteOnly]
    valid_custom_actions = ["create", "remove", "up", "down", "top", "bottom"]

    @extend_schema(
        responses={
            200: OpenApiResponse(PlaylistSerializer()),
            404: OpenApiResponse(
                ErrorResponseSerializer(), description="playlist not found"
            ),
        },
    )
    def get(self, request, playlist_id):
        # pylint: disable=unused-argument
        """get playlist"""
        self.get_document(playlist_id)
        if not self.response:
            error = ErrorResponseSerializer({"error": "playlist not found"})
            return Response(error.data, status=404)

        response_serializer = PlaylistSerializer(self.response)

        return Response(response_serializer.data)

    @extend_schema(
        request=PlaylistSingleUpdate(),
        responses={
            200: OpenApiResponse(PlaylistSerializer()),
            404: OpenApiResponse(
                ErrorResponseSerializer(), description="playlist not found"
            ),
        },
    )
    def post(self, request, playlist_id):
        """update subscribed state of playlist"""
        data_serializer = PlaylistSingleUpdate(data=request.data)
        data_serializer.is_valid(raise_exception=True)
        validated_data = data_serializer.validated_data

        self.get_document(playlist_id)
        if not self.response:
            error = ErrorResponseSerializer({"error": "playlist not found"})
            return Response(error.data, status=404)

        if self.response["playlist_type"] == "custom":
            error = ErrorResponseSerializer(
                {"error": f"playlist with ID {playlist_id} is custom"}
            )
            return Response(error.data, status=400)

        subscribed = validated_data.get("playlist_subscribed")
        sort_order = validated_data.get("playlist_sort_order")

        json_data = None
        if subscribed is not None:
            json_data = YoutubePlaylist(playlist_id).change_subscribe(
                new_subscribe_state=subscribed
            )

        if sort_order:
            json_data = YoutubePlaylist(playlist_id).change_sort_order(
                new_sort_order=sort_order
            )

        if not json_data:
            error = ErrorResponseSerializer(
                {"error": "expect playlist_subscribed or playlist_sort_order"}
            )
            return Response(error.data, status=400)

        response_serializer = PlaylistSerializer(json_data)
        return Response(response_serializer.data)

    @extend_schema(
        parameters=[PlaylistDeleteQuerySerializer],
        responses={
            204: OpenApiResponse(description="playlist deleted"),
        },
    )
    def delete(self, request, playlist_id):
        """delete playlist"""
        print(f"{playlist_id}: delete playlist")

        query_serializer = PlaylistDeleteQuerySerializer(
            data=request.query_params
        )
        query_serializer.is_valid(raise_exception=True)
        validated_query = query_serializer.validated_data

        delete_videos = validated_query.get("delete_videos", False)

        if delete_videos:
            YoutubePlaylist(playlist_id).delete_videos_playlist()
        else:
            YoutubePlaylist(playlist_id).delete_metadata()

        return Response(status=204)
