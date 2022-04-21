import os

from django.contrib.auth.middleware import RemoteUserMiddleware


class CustomRemoteUserMiddleware(RemoteUserMiddleware):
    header = os.environ.get('DJANGO_REMOTE_USER_HEADER', RemoteUserMiddleware.header)
