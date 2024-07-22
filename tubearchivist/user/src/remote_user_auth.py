from django.conf import settings
from django.contrib.auth.middleware import PersistentRemoteUserMiddleware


class HttpRemoteUserMiddleware(PersistentRemoteUserMiddleware):
    """This class allows authentication via HTTP_REMOTE_USER which is set for
    example by certain SSO applications.
    """

    header = settings.TA_AUTH_PROXY_USERNAME_HEADER
