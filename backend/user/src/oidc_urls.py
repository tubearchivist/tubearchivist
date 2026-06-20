"""OIDC URL routes using TubeArchivist's host-pinned views

Mirrors mozilla_django_oidc.urls (same view names) but swaps in the views that
anchor redirect_uri to TA_HOST.
"""

from django.urls import path
from user.src.oidc_views import (
    TAOIDCAuthenticationCallbackView,
    TAOIDCAuthenticationRequestView,
)

urlpatterns = [
    path(
        "callback/",
        TAOIDCAuthenticationCallbackView.as_view(),
        name="oidc_authentication_callback",
    ),
    path(
        "authenticate/",
        TAOIDCAuthenticationRequestView.as_view(),
        name="oidc_authentication_init",
    ),
]
