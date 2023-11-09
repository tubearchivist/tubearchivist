""" all home app urls """

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LogoutView
from django.shortcuts import redirect
from django.urls import path
from home import views

if hasattr(settings, "TA_AUTH_PROXY_LOGOUT_URL"):
    logout_path = path(
        "logout/",
        lambda request: redirect(
            settings.TA_AUTH_PROXY_LOGOUT_URL, permanent=False
        ),
        name="logout",
    )
else:
    logout_path = path(
        "logout/",
        LogoutView.as_view(),
        {"next_page": settings.LOGOUT_REDIRECT_URL},
        name="logout",
    )

urlpatterns = [
    path("", login_required(views.HomeView.as_view()), name="home"),
    path("login/", views.LoginView.as_view(), name="login"),
    logout_path,
    path("about/", views.AboutView.as_view(), name="about"),
    path(
        "downloads/",
        login_required(views.DownloadView.as_view()),
        name="downloads",
    ),
    path(
        "settings/",
        login_required(views.SettingsView.as_view()),
        name="settings",
    ),
    path(
        "settings/user/",
        login_required(views.SettingsUserView.as_view()),
        name="settings_user",
    ),
    path(
        "settings/application/",
        login_required(views.SettingsApplicationView.as_view()),
        name="settings_application",
    ),
    path(
        "settings/scheduling/",
        login_required(views.SettingsSchedulingView.as_view()),
        name="settings_scheduling",
    ),
    path(
        "settings/actions/",
        login_required(views.SettingsActionsView.as_view()),
        name="settings_actions",
    ),
    path(
        "channel/",
        login_required(views.ChannelView.as_view()),
        name="channel",
    ),
    path(
        "channel/<slug:channel_id>/",
        login_required(views.ChannelIdView.as_view()),
        name="channel_id",
    ),
    path(
        "channel/<slug:channel_id>/streams/",
        login_required(views.ChannelIdLiveView.as_view()),
        name="channel_id_live",
    ),
    path(
        "channel/<slug:channel_id>/shorts/",
        login_required(views.ChannelIdShortsView.as_view()),
        name="channel_id_shorts",
    ),
    path(
        "channel/<slug:channel_id>/about/",
        login_required(views.ChannelIdAboutView.as_view()),
        name="channel_id_about",
    ),
    path(
        "channel/<slug:channel_id>/playlist/",
        login_required(views.ChannelIdPlaylistView.as_view()),
        name="channel_id_playlist",
    ),
    path(
        "video/<slug:video_id>/",
        login_required(views.VideoView.as_view()),
        name="video",
    ),
    path(
        "playlist/",
        login_required(views.PlaylistView.as_view()),
        name="playlist",
    ),
    path(
        "playlist/<slug:playlist_id>/",
        login_required(views.PlaylistIdView.as_view()),
        name="playlist_id",
    ),
    path("search/", login_required(views.SearchView.as_view()), name="search"),
]
