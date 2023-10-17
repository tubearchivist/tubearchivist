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

    HOST_UID: int = int(os.environ.get("HOST_UID", False))
    HOST_GID: int = int(os.environ.get("HOST_GID", False))
    ENABLE_CAST: bool = bool(os.environ.get("ENABLE_CAST"))
    MEDIA_DIR: str = str(os.environ.get("TA_MEDIA_DIR", "/youtube"))
    APP_DIR: str = str(os.environ.get("TA_APP_DIR", "/app"))
    CACHE_DIR: str = str(os.environ.get("TA_CACHE_DIR", "/cache"))
