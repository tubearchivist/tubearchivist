"""all api urls"""

from api.views import (
    ChannelApiListView,
    ChannelApiView,
    DownloadApiListView,
    DownloadApiView,
    LoginApiView,
    PingView,
    PlaylistApiView,
    VideoApiListView,
    VideoApiView,
    VideoProgressView,
    VideoSponsorView,
)
from django.urls import path

urlpatterns = [
    path("ping/", PingView.as_view(), name="ping"),
    path("login/", LoginApiView.as_view(), name="api-login"),
    path(
        "video/",
        VideoApiListView.as_view(),
        name="api-video-list",
    ),
    path(
        "video/<slug:video_id>/",
        VideoApiView.as_view(),
        name="api-video",
    ),
    path(
        "video/<slug:video_id>/progress/",
        VideoProgressView.as_view(),
        name="api-video-progress",
    ),
    path(
        "video/<slug:video_id>/sponsor/",
        VideoSponsorView.as_view(),
        name="api-video-sponsor",
    ),
    path(
        "channel/",
        ChannelApiListView.as_view(),
        name="api-channel-list",
    ),
    path(
        "channel/<slug:channel_id>/",
        ChannelApiView.as_view(),
        name="api-channel",
    ),
    path(
        "playlist/<slug:playlist_id>/",
        PlaylistApiView.as_view(),
        name="api-playlist",
    ),
    path(
        "download/",
        DownloadApiListView.as_view(),
        name="api-download-list",
    ),
    path(
        "download/<slug:video_id>/",
        DownloadApiView.as_view(),
        name="api-download",
    ),
]
