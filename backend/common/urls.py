"""all api urls"""

from common import views
from django.urls import path

urlpatterns = [
    path("ping/", views.PingView.as_view(), name="ping"),
    path(
        "refresh/",
        views.RefreshView.as_view(),
        name="api-refresh",
    ),
    path(
        "watched/",
        views.WatchedView.as_view(),
        name="api-watched",
    ),
    path(
        "search/",
        views.SearchView.as_view(),
        name="api-search",
    ),
    path(
        "notification/",
        views.NotificationView.as_view(),
        name="api-notification",
    ),
]
