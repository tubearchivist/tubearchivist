"""all api urls"""

from api import views
from django.urls import path

urlpatterns = [
    path("ping/", views.PingView.as_view(), name="ping"),
    path("login/", views.LoginApiView.as_view(), name="api-login"),
    path(
        "refresh/",
        views.RefreshView.as_view(),
        name="api-refresh",
    ),
    path(
        "config/user/",
        views.UserConfigView.as_view(),
        name="api-config-user",
    ),
    path(
        "watched/",
        views.WatchedView.as_view(),
        name="api-watched",
    ),
    path(
        "search/",
        views.SearchView.as_view(),
        name="api-search",
    ),
    path(
        "notification/",
        views.NotificationView.as_view(),
        name="api-notification",
    ),
    path(
        "stats/video/",
        views.StatVideoView.as_view(),
        name="api-stats-video",
    ),
    path(
        "stats/channel/",
        views.StatChannelView.as_view(),
        name="api-stats-channel",
    ),
    path(
        "stats/playlist/",
        views.StatPlaylistView.as_view(),
        name="api-stats-playlist",
    ),
    path(
        "stats/download/",
        views.StatDownloadView.as_view(),
        name="api-stats-download",
    ),
    path(
        "stats/watch/",
        views.StatWatchProgress.as_view(),
        name="api-stats-watch",
    ),
    path(
        "stats/downloadhist/",
        views.StatDownloadHist.as_view(),
        name="api-stats-downloadhist",
    ),
    path(
        "stats/biggestchannels/",
        views.StatBiggestChannel.as_view(),
        name="api-stats-biggestchannels",
    ),
]
