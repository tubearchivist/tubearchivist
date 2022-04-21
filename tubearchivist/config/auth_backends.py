import os

from django.contrib.auth.backends import RemoteUserBackend


class CustomRemoteUserBackend(RemoteUserBackend):

    create_unknown_user = str(os.environ.get(
        'DJANGO_REMOTE_USER_CREATE_UNKNOWN_USER',
        RemoteUserBackend.create_unknown_user)
    ).lower().startswith('t')
