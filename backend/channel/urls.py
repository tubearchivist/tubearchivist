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
        "<slug:channel_id>/aggs/",
        views.ChannelAggsApiView.as_view(),
        name="api-channel-aggs",
    ),
    path(
        "<slug:channel_id>/nav/",
        views.ChannelNavApiView.as_view(),
        name="api-channel-nav",
    ),
]
