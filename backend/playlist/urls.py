"""all playlist API urls"""

from django.urls import path
from playlist import views

urlpatterns = [
    path(
        "",
        views.PlaylistApiListView.as_view(),
        name="api-playlist-list",
    ),
    path(
        "custom/",
        views.PlaylistCustomApiListView.as_view(),
        name="api-custom-playlist-list",
    ),
    path(
        "custom/<slug:playlist_id>/",
        views.PlaylistCustomApiView.as_view(),
        name="api-custom-playlist",
    ),
    path(
        "<slug:playlist_id>/",
        views.PlaylistApiView.as_view(),
        name="api-playlist",
    ),
]
