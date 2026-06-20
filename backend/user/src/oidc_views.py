"""OIDC views that anchor the redirect_uri to the configured public host

TubeArchivist serves behind its own nginx (which rewrites the Host header to
localhost) and usually an external TLS-terminating proxy (which rewrites the
scheme). Letting mozilla-django-oidc infer the callback URL from the request
therefore produces a wrong redirect_uri such as ``http://localhost/...``. We
pin it to TA_HOST, the documented public URL, so the authorize redirect_uri and
the token-exchange redirect_uri are both correct and identical.
"""

from django.conf import settings
from mozilla_django_oidc.views import (
    OIDCAuthenticationCallbackView,
    OIDCAuthenticationRequestView,
)


class PublicHostRedirectMixin:
    """build root-relative absolute URIs from TA_OIDC_PUBLIC_URL

    mozilla-django-oidc resolves the redirect_uri via
    ``request.build_absolute_uri(reverse(...))`` in both the request view and
    the auth backend's token exchange. Patching it on the request object covers
    both, since the backend reuses the same request.
    """

    def dispatch(self, request, *args, **kwargs):
        base = getattr(settings, "TA_OIDC_PUBLIC_URL", "")
        if base:
            original = request.build_absolute_uri

            def build_absolute_uri(location=None):
                if location and location.startswith("/"):
                    return base.rstrip("/") + location
                return original(location)

            request.build_absolute_uri = build_absolute_uri

        return super().dispatch(request, *args, **kwargs)


class TAOIDCAuthenticationRequestView(
    PublicHostRedirectMixin, OIDCAuthenticationRequestView
):
    """authorize redirect with a TA_HOST-anchored redirect_uri"""


class TAOIDCAuthenticationCallbackView(
    PublicHostRedirectMixin, OIDCAuthenticationCallbackView
):
    """callback whose token-exchange redirect_uri matches the authorize one"""
