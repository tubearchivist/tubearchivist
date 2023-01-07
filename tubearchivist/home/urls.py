""" all home app urls """

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LogoutView
from django.urls import path
from home.views import (
    AboutView,
    ChannelIdAboutView,
    ChannelIdLiveView,
    ChannelIdPlaylistView,
    ChannelIdShortsView,
    ChannelIdView,
    ChannelView,
    DownloadView,
    HomeView,
    LoginView,
    PlaylistIdView,
    PlaylistView,
    SearchView,
    SettingsView,
    VideoView,
    process,
    progress,
)

urlpatterns = [
    path("", login_required(HomeView.as_view()), name="home"),
    path("login/", LoginView.as_view(), name="login"),
    path(
        "logout/",
        LogoutView.as_view(),
        {"next_page": settings.LOGOUT_REDIRECT_URL},
        name="logout",
    ),
    path("about/", AboutView.as_view(), name="about"),
    path(
        "downloads/", login_required(DownloadView.as_view()), name="downloads"
    ),
    path("settings/", login_required(SettingsView.as_view()), name="settings"),
    path("process/", login_required(process), name="process"),
    path("progress/", login_required(progress), name="progress"),
    path("channel/", login_required(ChannelView.as_view()), name="channel"),
    path(
        "channel/<slug:channel_id>/",
        login_required(ChannelIdView.as_view()),
        name="channel_id",
    ),
    path(
        "channel/<slug:channel_id>/streams/",
        login_required(ChannelIdLiveView.as_view()),
        name="channel_id_live",
    ),
    path(
        "channel/<slug:channel_id>/shorts/",
        login_required(ChannelIdShortsView.as_view()),
        name="channel_id_shorts",
    ),
    path(
        "channel/<slug:channel_id>/about/",
        login_required(ChannelIdAboutView.as_view()),
        name="channel_id_about",
    ),
    path(
        "channel/<slug:channel_id>/playlist/",
        login_required(ChannelIdPlaylistView.as_view()),
        name="channel_id_playlist",
    ),
    path(
        "video/<slug:video_id>/",
        login_required(VideoView.as_view()),
        name="video",
    ),
    path("playlist/", login_required(PlaylistView.as_view()), name="playlist"),
    path(
        "playlist/<slug:playlist_id>/",
        login_required(PlaylistIdView.as_view()),
        name="playlist_id",
    ),
    path("search/", login_required(SearchView.as_view()), name="search"),
]
