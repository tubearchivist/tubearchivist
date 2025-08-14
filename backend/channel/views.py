"""all channel API views"""

from channel.serializers import (
    ChannelAggSerializer,
    ChannelListQuerySerializer,
    ChannelListSerializer,
    ChannelNavSerializer,
    ChannelSearchQuerySerializer,
    ChannelSerializer,
    ChannelUpdateSerializer,
)
from channel.src.index import YoutubeChannel, channel_overwrites
from channel.src.nav import ChannelNav
from common.serializers import ErrorResponseSerializer
from common.src.urlparser import Parser
from common.views_base import AdminWriteOnly, ApiBaseView
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
)
from rest_framework.response import Response
from task.tasks import index_channel_playlists, subscribe_to


class ChannelApiListView(ApiBaseView):
    """resolves to /api/channel/
    GET: returns list of channels
    POST: edit a list of channels
    """

    search_base = "ta_channel/_search/"
    valid_filter = ["subscribed"]
    permission_classes = [AdminWriteOnly]

    @extend_schema(
        responses={
            200: OpenApiResponse(ChannelListSerializer()),
        },
        parameters=[ChannelListQuerySerializer()],
    )
    def get(self, request):
        """get request"""
        self.data.update(
            {"sort": [{"channel_name.keyword": {"order": "asc"}}]}
        )

        serializer = ChannelListQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        must_list = []
        query_filter = validated_data.get("filter")
        if query_filter is not None:
            channel_subscribed = query_filter == "subscribed"
            must_list.append(
                {"term": {"channel_subscribed": {"value": channel_subscribed}}}
            )

        self.data["query"] = {"bool": {"must": must_list}}
        self.get_document_list(request)
        serializer = ChannelListSerializer(self.response)

        return Response(serializer.data)

    def post(self, request):
        """subscribe/unsubscribe to list of channels"""
        data = request.data
        try:
            to_add = data["data"]
        except KeyError:
            message = "missing expected data key"
            print(message)
            return Response({"message": message}, status=400)

        pending = []
        for channel_item in to_add:
            channel_id = channel_item["channel_id"]
            if channel_item["channel_subscribed"]:
                pending.append(channel_id)
            else:
                self._unsubscribe(channel_id)

        if pending:
            url_str = " ".join(pending)
            subscribe_to.delay(url_str, expected_type="channel")

        return Response(data)

    @staticmethod
    def _unsubscribe(channel_id: str):
        """unsubscribe"""
        print(f"[{channel_id}] unsubscribe from channel")
        YoutubeChannel(channel_id).change_subscribe(new_subscribe_state=False)


class ChannelApiView(ApiBaseView):
    """resolves to /api/channel/<channel_id>/
    GET: returns metadata dict of channel
    """

    search_base = "ta_channel/_doc/"
    permission_classes = [AdminWriteOnly]

    @extend_schema(
        responses={
            200: OpenApiResponse(ChannelSerializer()),
            404: OpenApiResponse(
                ErrorResponseSerializer(), description="Channel not found"
            ),
        }
    )
    def get(self, request, channel_id):
        # pylint: disable=unused-argument
        """get channel detail"""
        self.get_document(channel_id)
        if not self.response:
            error = ErrorResponseSerializer({"error": "channel not found"})
            return Response(error.data, status=404)

        response_serializer = ChannelSerializer(self.response)
        return Response(response_serializer.data, status=self.status_code)

    @extend_schema(
        request=ChannelUpdateSerializer(),
        responses={
            200: OpenApiResponse(ChannelUpdateSerializer()),
            400: OpenApiResponse(
                ErrorResponseSerializer(), description="Bad request"
            ),
            404: OpenApiResponse(
                ErrorResponseSerializer(), description="Channel not found"
            ),
        },
    )
    def post(self, request, channel_id):
        """modify channel"""
        self.get_document(channel_id)
        if not self.response:
            error = ErrorResponseSerializer({"error": "channel not found"})
            return Response(error.data, status=404)

        serializer = ChannelUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        subscribed = validated_data.get("channel_subscribed")
        if subscribed is not None:
            YoutubeChannel(channel_id).change_subscribe(
                new_subscribe_state=subscribed
            )

        overwrites = validated_data.get("channel_overwrites")
        if overwrites:
            channel_overwrites(channel_id, overwrites)
            if overwrites.get("index_playlists"):
                index_channel_playlists.delay(channel_id)

        return Response(serializer.data, status=200)

    @extend_schema(
        responses={
            204: OpenApiResponse(description="Channel deleted"),
            404: OpenApiResponse(
                ErrorResponseSerializer(), description="Channel not found"
            ),
        },
    )
    def delete(self, request, channel_id):
        # pylint: disable=unused-argument
        """delete channel"""
        try:
            YoutubeChannel(channel_id).delete_channel()
            return Response(status=204)
        except FileNotFoundError:
            pass

        error = ErrorResponseSerializer({"error": "channel not found"})
        return Response(error.data, status=404)


class ChannelAggsApiView(ApiBaseView):
    """resolves to /api/channel/<channel_id>/aggs/
    GET: get channel aggregations
    """

    search_base = "ta_video/_search"

    @extend_schema(
        responses={
            200: OpenApiResponse(ChannelAggSerializer()),
        },
    )
    def get(self, request, channel_id):
        """get channel aggregations"""
        self.data.update(
            {
                "query": {
                    "term": {"channel.channel_id": {"value": channel_id}}
                },
                "aggs": {
                    "total_items": {"value_count": {"field": "youtube_id"}},
                    "total_size": {"sum": {"field": "media_size"}},
                    "total_duration": {"sum": {"field": "player.duration"}},
                },
            }
        )
        self.get_aggs()
        serializer = ChannelAggSerializer(self.response)

        return Response(serializer.data)


class ChannelNavApiView(ApiBaseView):
    """resolves to /api/channel/<channel_id>/nav/
    GET: get channel nav
    """

    @extend_schema(
        responses={
            200: OpenApiResponse(ChannelNavSerializer()),
        },
    )
    def get(self, request, channel_id):
        """get navigation"""

        nav = ChannelNav(channel_id).get_nav()
        serializer = ChannelNavSerializer(nav)
        return Response(serializer.data)


class ChannelApiSearchView(ApiBaseView):
    """resolves to /api/channel/search/
    search for channel
    """

    search_base = "ta_channel/_doc/"

    @extend_schema(
        responses={
            200: OpenApiResponse(ChannelSerializer()),
            400: OpenApiResponse(description="Bad Request"),
            404: OpenApiResponse(
                ErrorResponseSerializer(), description="Channel not found"
            ),
        },
        parameters=[
            OpenApiParameter(
                name="q",
                description="Search query string",
                required=True,
                type=str,
            ),
        ],
    )
    def get(self, request):
        """search for local channel ID"""

        serializer = ChannelSearchQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        query = validated_data.get("q")
        if not query:
            message = "missing expected q parameter"
            return Response({"message": message, "data": False}, status=400)

        try:
            parsed = Parser(query).parse()[0]
        except (ValueError, IndexError, AttributeError):
            error = ErrorResponseSerializer(
                {"error": f"channel not found: {query}"}
            )
            return Response(error.data, status=404)

        if not parsed["type"] == "channel":
            error = ErrorResponseSerializer({"error": "expected channel data"})
            return Response(error.data, status=400)

        self.get_document(parsed["url"])
        serializer = ChannelSerializer(self.response)

        return Response(serializer.data, status=self.status_code)
