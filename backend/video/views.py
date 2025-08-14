"""all API views for video endpoints"""

from common.serializers import ErrorResponseSerializer
from common.src.helper import calc_is_watched
from common.src.ta_redis import RedisArchivist
from common.src.watched import WatchState
from common.views_base import AdminWriteOnly, ApiBaseView
from drf_spectacular.utils import OpenApiResponse, extend_schema
from playlist.src.index import YoutubePlaylist
from rest_framework.response import Response
from video.serializers import (
    CommentItemSerializer,
    PlayerSerializer,
    PlaylistNavItemSerializer,
    VideoListQuerySerializer,
    VideoListSerializer,
    VideoProgressUpdateSerializer,
    VideoSerializer,
)
from video.src.index import YoutubeVideo
from video.src.query_building import QueryBuilder


class VideoApiListView(ApiBaseView):
    """resolves to /api/video/
    GET: returns list of videos
    params:
    - playlist:str=<playlist-id>
    - channel:str=<channel-id>
    - watch:enum=watched|unwatched|continue
    - sort:enum=published|downloaded|views|likes|duration|filesize
    - order:enum=asc|desc
    - type:enum=videos|streams|shorts
    - height:int=px
    """

    search_base = "ta_video/_search/"

    @extend_schema(
        parameters=[VideoListQuerySerializer()],
        responses={
            200: VideoListSerializer(),
            400: OpenApiResponse(
                ErrorResponseSerializer(), description="bad request"
            ),
        },
    )
    def get(self, request):
        """get video list"""
        query_serializer = VideoListQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        validated_query = query_serializer.validated_data

        data = QueryBuilder(request.user.id, **validated_query).build_data()
        if data == {"query": {"bool": {"must": [None]}}}:
            # skip empty lookup
            return Response([])

        self.data = data
        self.get_document_list(request, progress_match=request.user.id)

        response_serializer = VideoListSerializer(self.response)

        return Response(response_serializer.data)


class VideoApiView(ApiBaseView):
    """resolves to /api/video/<video_id>/
    GET: returns metadata dict of video
    """

    search_base = "ta_video/_doc/"
    permission_classes = [AdminWriteOnly]

    @extend_schema(
        responses={
            200: VideoSerializer(),
            404: OpenApiResponse(
                ErrorResponseSerializer(), description="video not found"
            ),
        },
    )
    def get(self, request, video_id):
        """get video"""
        self.get_document(video_id, progress_match=request.user.id)
        if not self.response:
            error = ErrorResponseSerializer({"error": "video not found"})
            return Response(error.data, status=404)

        serializer = VideoSerializer(self.response)
        return Response(serializer.data)

    @extend_schema(
        responses={
            204: OpenApiResponse(description="video deleted"),
            404: OpenApiResponse(
                ErrorResponseSerializer(), description="video not found"
            ),
        }
    )
    def delete(self, request, video_id):
        # pylint: disable=unused-argument
        """delete video"""
        try:
            YoutubeVideo(video_id).delete_media_file()
        except FileNotFoundError:
            error = ErrorResponseSerializer({"error": "video not found"})
            return Response(error.data, status=404)

        return Response(status=204)


class VideoCommentView(ApiBaseView):
    """resolves to /api/video/<video_id>/comment/
    handle video comments
    GET: return all comments from video with reply threads
    """

    search_base = "ta_comment/_doc/"

    @extend_schema(
        responses={
            200: CommentItemSerializer(),
            404: OpenApiResponse(
                ErrorResponseSerializer(), description="video not found"
            ),
        }
    )
    def get(self, request, video_id):
        """get video comments"""
        # pylint: disable=unused-argument
        self.get_document(video_id)
        if self.status_code == 404:
            error = ErrorResponseSerializer({"error": "video not found"})
            return Response(error.data, status=404)

        serializer = CommentItemSerializer(self.response, many=True)

        return Response(serializer.data)


class VideoApiNavView(ApiBaseView):
    """resolves to /api/video/<video-id>/nav/
    GET: returns playlist nav
    """

    search_base = "ta_video/_doc/"

    @extend_schema(
        responses={
            200: PlaylistNavItemSerializer(),
            404: OpenApiResponse(
                ErrorResponseSerializer(), description="video not found"
            ),
        }
    )
    def get(self, request, video_id):
        # pylint: disable=unused-argument
        """get video playlist nav"""
        self.get_document(video_id)
        if self.status_code == 404:
            error = ErrorResponseSerializer({"error": "video not found"})
            return Response(error.data, status=404)

        playlist_nav = []

        if not self.response.get("playlist"):
            return Response(playlist_nav)

        for playlist_id in self.response["playlist"]:
            playlist = YoutubePlaylist(playlist_id)
            playlist.get_from_es()
            playlist.build_nav(video_id)
            if playlist.nav:
                playlist_nav.append(playlist.nav)

        response_serializer = PlaylistNavItemSerializer(
            playlist_nav, many=True
        )

        return Response(response_serializer.data)


class VideoProgressView(ApiBaseView):
    """resolves to /api/video/<video_id>/progress/
    handle progress status for video
    """

    search_base = "ta_video/_doc/"

    @staticmethod
    def _get_key(user_id: int, video_id: str) -> str:
        """redis key"""
        return f"{user_id}:progress:{video_id}"

    @extend_schema(
        request=VideoProgressUpdateSerializer(),
        responses={
            200: PlayerSerializer(),
            404: OpenApiResponse(
                ErrorResponseSerializer(), description="video not found"
            ),
        },
    )
    def post(self, request, video_id):
        """set video progress position in redis"""
        data_serializer = VideoProgressUpdateSerializer(data=request.data)
        data_serializer.is_valid(raise_exception=True)
        validated_data = data_serializer.validated_data

        self.get_document(video_id)
        if self.status_code == 404:
            error = ErrorResponseSerializer({"error": "video not found"})
            return Response(error.data, status=404)

        position = validated_data["position"]
        key = self._get_key(request.user.id, video_id)
        redis_con = RedisArchivist()
        current_progress = (
            redis_con.get_message_dict(key) or self.response["player"]
        )

        current_progress.update({"position": position, "youtube_id": video_id})
        watched = self._check_watched(request, video_id, current_progress)
        if watched:
            expire = 60
        else:
            expire = False

        current_progress.update({"watched": watched})
        if position > 5:
            redis_con.set_message(key, current_progress, expire=expire)

        response_serializer = PlayerSerializer(current_progress)

        return Response(response_serializer.data)

    def _check_watched(self, request, video_id, current_progress) -> bool:
        """check watched state"""
        if current_progress["watched"]:
            return True

        watched = calc_is_watched(
            current_progress["duration"], current_progress["position"]
        )
        if watched:
            WatchState(video_id, watched, request.user.id).change()

        return watched

    @extend_schema(
        responses={
            204: OpenApiResponse(description="video progress deleted"),
        }
    )
    def delete(self, request, video_id):
        """delete progress position"""
        key = self._get_key(request.user.id, video_id)
        RedisArchivist().del_message(key)

        return Response(status=204)


class VideoSimilarView(ApiBaseView):
    """resolves to /api/video/<video-id>/similar/
    GET: return max 6 videos similar to this
    """

    search_base = "ta_video/_search/"

    @extend_schema(
        responses=VideoSerializer(many=True),
    )
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
        serializer = VideoSerializer(self.response["data"], many=True)
        return Response(serializer.data)
