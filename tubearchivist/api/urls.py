"""all api urls"""

from api.views import (
    ChannelApiView,
    DownloadApiListView,
    DownloadApiView,
    PlaylistApiView,
    VideoApiView,
)
from django.urls import path

urlpatterns = [
    path(
        "video/<slug:video_id>/",
        VideoApiView.as_view(),
        name="api-video",
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
