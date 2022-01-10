"""all api urls"""

from api.views import (
    ChannelApiView,
    DownloadApiView,
    PlaylistApiView,
    VideoApiView,
)
from django.contrib.auth.decorators import login_required
from django.urls import path

urlpatterns = [
    path(
        "video/<slug:video_id>/",
        login_required(VideoApiView.as_view()),
        name="api-video",
    ),
    path(
        "channel/<slug:channel_id>/",
        login_required(ChannelApiView.as_view()),
        name="api-channel",
    ),
    path(
        "playlist/<slug:playlist_id>/",
        login_required(PlaylistApiView.as_view()),
        name="api-playlist",
    ),
    path(
        "download/<slug:video_id>/",
        login_required(DownloadApiView.as_view()),
        name="api-download",
    ),
]
