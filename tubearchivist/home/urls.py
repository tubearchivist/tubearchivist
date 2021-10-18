""" all home app urls """

from django.urls import path
from home.views import (
    AboutView,
    ChannelIdView,
    ChannelView,
    DownloadView,
    HomeView,
    LoginView,
    SettingsView,
    VideoView,
)

from . import views

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("login/", LoginView.as_view(), name="login"),
    path("about/", AboutView.as_view(), name="about"),
    path("downloads/", DownloadView.as_view(), name="downloads"),
    path("settings/", SettingsView.as_view(), name="settings"),
    path("process/", views.process, name="process"),
    path("downloads/progress/", views.progress, name="progress"),
    path("channel/", ChannelView.as_view(), name="channel"),
    path(
        "channel/<slug:channel_id_detail>/",
        ChannelIdView.as_view(),
        name="channel_id",
    ),
    path("video/<slug:video_id>/", VideoView.as_view(), name="video"),
]
