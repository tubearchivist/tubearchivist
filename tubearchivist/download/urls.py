"""all download API urls"""

from django.urls import path
from download import views

urlpatterns = [
    path("", views.DownloadApiListView.as_view(), name="api-download-list"),
    path(
        "<slug:video_id>/",
        views.DownloadApiView.as_view(),
        name="api-download",
    ),
]
