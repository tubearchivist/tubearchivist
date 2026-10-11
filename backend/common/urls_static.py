"""static urls"""

from common import views_static
from django.urls import path

urlpatterns = [
    path(
        "stream/<slug:channel_id>/<slug:video_id>.mp4",
        views_static.MediaStreamView.as_view(),
        name="stream",
    ),
    path(
        "subtitle/<slug:channel_id>/<slug:video_id>.<slug:lang>.vtt",
        views_static.SubtitleView.as_view(),
        name="subtitle",
    ),
    path(
        "thumb/video/<slug:video_id>.jpg",
        views_static.VideoThumbView.as_view(),
        name="video-thumb",
    ),
    path(
        "thumb/channel/<slug:channel_id>/<slug:art_type>.jpg",
        views_static.ChannelArtView.as_view(),
        name="channel-art",
    ),
    path(
        "thumb/playlist/<slug:playlist_id>.jpg",
        views_static.PlaylistThumbView.as_view(),
        name="playlist-thumb",
    ),
]
