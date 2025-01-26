"""all stats API views"""

from common.views_base import ApiBaseView
from rest_framework.response import Response
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
