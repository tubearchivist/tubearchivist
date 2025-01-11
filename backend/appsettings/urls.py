"""all app settings API urls"""

from appsettings import views
from django.urls import path

urlpatterns = [
    path(
        "config/",
        views.AppConfigApiView.as_view(),
        name="api-config",
    ),
    path(
        "snapshot/",
        views.SnapshotApiListView.as_view(),
        name="api-snapshot-list",
    ),
    path(
        "snapshot/<slug:snapshot_id>/",
        views.SnapshotApiView.as_view(),
        name="api-snapshot",
    ),
    path(
        "backup/",
        views.BackupApiListView.as_view(),
        name="api-backup-list",
    ),
    path(
        "backup/<str:filename>/",
        views.BackupApiView.as_view(),
        name="api-backup",
    ),
    path(
        "cookie/",
        views.CookieView.as_view(),
        name="api-cookie",
    ),
    path(
        "potoken/",
        views.POTokenView.as_view(),
        name="api-potoken",
    ),
    path(
        "token/",
        views.TokenView.as_view(),
        name="api-token",
    ),
]
