"""all stats API urls"""

from django.urls import path
from stats import views

urlpatterns = [
    path(
        "video/",
        views.StatVideoView.as_view(),
        name="api-stats-video",
    ),
    path(
        "channel/",
        views.StatChannelView.as_view(),
        name="api-stats-channel",
    ),
    path(
        "playlist/",
        views.StatPlaylistView.as_view(),
        name="api-stats-playlist",
    ),
    path(
        "download/",
        views.StatDownloadView.as_view(),
        name="api-stats-download",
    ),
    path(
        "watch/",
        views.StatWatchProgress.as_view(),
        name="api-stats-watch",
    ),
    path(
        "downloadhist/",
        views.StatDownloadHist.as_view(),
        name="api-stats-downloadhist",
    ),
    path(
        "biggestchannels/",
        views.StatBiggestChannel.as_view(),
        name="api-stats-biggestchannels",
    ),
]
