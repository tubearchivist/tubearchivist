"""all channel API urls"""

from channel import views
from django.urls import path

urlpatterns = [
    path(
        "",
        views.ChannelApiListView.as_view(),
        name="api-channel-list",
    ),
    path(
        "search/",
        views.ChannelApiSearchView.as_view(),
        name="api-channel-search",
    ),
    path(
        "<slug:channel_id>/",
        views.ChannelApiView.as_view(),
        name="api-channel",
    ),
    path(
        "<slug:channel_id>/video/",
        views.ChannelApiVideoView.as_view(),
        name="api-channel-video",
    ),
]
