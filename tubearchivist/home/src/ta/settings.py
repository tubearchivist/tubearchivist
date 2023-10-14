"""
Functionality:
- read and write application config backed by ES
- encapsulate persistence of application properties
"""
import os


class EnvironmentSettings:
    """
    Handle settings for the application that are driven from the environment.
    These will not change when the user is using the application.
    These settings are only provided only on startup.
    """

    def __init__(self) -> None:
        # read environment application variables
        self._host_uid: int = int(os.environ.get("HOST_UID", False))
        self._host_gid: int = int(os.environ.get("HOST_GID", False))
        self._enable_cast: bool = bool(os.environ.get("ENABLE_CAST"))

    def get_media_dir(self) -> str:
        return "/youtube"

    def get_app_root(self) -> str:
        return "/app"

    def get_cache_dir(self) -> str:
        return "/cache"

    def get_host_uid(self) -> int:
        return self._host_uid

    def get_host_gid(self) -> int:
        return self._host_gid

    def is_cast_enabled(self) -> bool:
        return self._enable_cast
