"""all app settings API urls"""

from appsettings import views, views_mb
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
        "token/",
        views.TokenView.as_view(),
        name="api-token",
    ),
    path(
        "rescan-filesystem/",
        views.RescanFileSystem.as_view(),
        name="api-rescan-filesystem",
    ),
    path(
        "manual-import/",
        views.ManualImportView.as_view(),
        name="api-manual-import",
    ),
    path(
        "membership/profile/",
        views_mb.MembershipProfileView.as_view(),
        name="api-membership-profile",
    ),
    path(
        "membership/sync/",
        views_mb.MembershipSubscriptionSync.as_view(),
        name="api-membership-sync",
    ),
    path(
        "membership/token/",
        views_mb.MembershipToken.as_view(),
        name="api-membership-token",
    ),
]
