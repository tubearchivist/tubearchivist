"""all api urls"""

from api import views
from django.urls import path

urlpatterns = [
    path("ping/", views.PingView.as_view(), name="ping"),
    path("login/", views.LoginApiView.as_view(), name="api-login"),
    path(
        "refresh/",
        views.RefreshView.as_view(),
        name="api-refresh",
    ),
    path(
        "config/user/",
        views.UserConfigView.as_view(),
        name="api-config-user",
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
