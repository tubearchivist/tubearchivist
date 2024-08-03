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
        "<slug:playlist_id>/",
        views.PlaylistApiView.as_view(),
        name="api-playlist",
    ),
]
