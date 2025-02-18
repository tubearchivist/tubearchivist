"""all stats API views"""

from common.serializers import ErrorResponseSerializer
from common.views_base import ApiBaseView
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.response import Response
from stats.serializers import (
    BiggestChannelItemSerializer,
    BiggestChannelQuerySerializer,
    ChannelStatsSerializer,
    DownloadHistItemSerializer,
    DownloadStatsSerializer,
    PlaylistStatsSerializer,
    VideoStatsSerializer,
    WatchStatsSerializer,
)
from stats.src.aggs import (
    BiggestChannel,
    Channel,
    Download,
    DownloadHist,
    Playlist,
    Video,
    WatchProgress,
)


class StatVideoView(ApiBaseView):
    """resolves to /api/stats/video/
    GET: return video stats
    """

    @extend_schema(responses=VideoStatsSerializer())
    def get(self, request):
        """get video stats"""
        # pylint: disable=unused-argument
        serializer = VideoStatsSerializer(Video().process())

        return Response(serializer.data)


class StatChannelView(ApiBaseView):
    """resolves to /api/stats/channel/
    GET: return channel stats
    """

    @extend_schema(responses=ChannelStatsSerializer())
    def get(self, request):
        """get channel stats"""
        # pylint: disable=unused-argument
        serializer = ChannelStatsSerializer(Channel().process())

        return Response(serializer.data)


class StatPlaylistView(ApiBaseView):
    """resolves to /api/stats/playlist/
    GET: return playlist stats
    """

    @extend_schema(responses=PlaylistStatsSerializer())
    def get(self, request):
        """get playlist stats"""
        # pylint: disable=unused-argument
        serializer = PlaylistStatsSerializer(Playlist().process())

        return Response(serializer.data)


class StatDownloadView(ApiBaseView):
    """resolves to /api/stats/download/
    GET: return download stats
    """

    @extend_schema(responses=DownloadStatsSerializer())
    def get(self, request):
        """get download stats"""
        # pylint: disable=unused-argument
        serializer = DownloadStatsSerializer(Download().process())

        return Response(serializer.data)


class StatWatchProgress(ApiBaseView):
    """resolves to /api/stats/watch/
    GET: return watch/unwatch progress stats
    """

    @extend_schema(responses=WatchStatsSerializer())
    def get(self, request):
        """get watched stats"""
        # pylint: disable=unused-argument
        serializer = WatchStatsSerializer(WatchProgress().process())

        return Response(serializer.data)


class StatDownloadHist(ApiBaseView):
    """resolves to /api/stats/downloadhist/
    GET: return download video count histogram for last days
    """

    @extend_schema(responses=DownloadHistItemSerializer(many=True))
    def get(self, request):
        """get download hist items"""
        # pylint: disable=unused-argument
        download_items = DownloadHist().process()
        serializer = DownloadHistItemSerializer(download_items, many=True)

        return Response(serializer.data)


class StatBiggestChannel(ApiBaseView):
    """resolves to /api/stats/biggestchannels/
    GET: return biggest channels
    param: order
    """

    @extend_schema(
        responses={
            200: OpenApiResponse(BiggestChannelItemSerializer(many=True)),
            400: OpenApiResponse(
                ErrorResponseSerializer(), description="Bad request"
            ),
        },
    )
    def get(self, request):
        """get biggest channels stats"""
        query_serializer = BiggestChannelQuerySerializer(
            data=request.query_params
        )
        query_serializer.is_valid(raise_exception=True)
        validated_query = query_serializer.validated_data
        order = validated_query["order"]

        channel_items = BiggestChannel(order).process()
        serializer = BiggestChannelItemSerializer(channel_items, many=True)

        return Response(serializer.data)
