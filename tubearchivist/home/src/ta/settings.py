"""
Functionality:
- read and write application config backed by ES
- encapsulate persistence of application properties
"""

from os import environ


class EnvironmentSettings:
    """
    Handle settings for the application that are driven from the environment.
    These will not change when the user is using the application.
    These settings are only provided only on startup.
    """

    HOST_UID: int = int(environ.get("HOST_UID", False))
    HOST_GID: int = int(environ.get("HOST_GID", False))
    ENABLE_CAST: bool = bool(environ.get("ENABLE_CAST"))
    TZ: str = str(environ.get("TZ", "UTC"))
    TA_PORT: int = int(environ.get("TA_PORT", False))
    TA_UWSGI_PORT: int = int(environ.get("TA_UWSGI_PORT", False))
    TA_USERNAME: str = str(environ.get("TA_USERNAME"))
    TA_PASSWORD: str = str(environ.get("TA_PASSWORD"))

    # Application Paths
    MEDIA_DIR: str = str(environ.get("TA_MEDIA_DIR", "/youtube"))
    APP_DIR: str = str(environ.get("TA_APP_DIR", "/app"))
    CACHE_DIR: str = str(environ.get("TA_CACHE_DIR", "/cache"))

    # Redis
    REDIS_HOST: str = str(environ.get("REDIS_HOST"))
    REDIS_PORT: int = int(environ.get("REDIS_PORT", 6379))
    REDIS_NAME_SPACE: str = str(environ.get("REDIS_NAME_SPACE", "ta:"))

    # ElasticSearch
    ES_URL: str = str(environ.get("ES_URL"))
    ES_PASS: str = str(environ.get("ELASTIC_PASSWORD"))
    ES_USER: str = str(environ.get("ELASTIC_USER", "elastic"))
    ES_SNAPSHOT_DIR: str = str(
        environ.get(
            "ES_SNAPSHOT_DIR", "/usr/share/elasticsearch/data/snapshot"
        )
    )
    ES_DISABLE_VERIFY_SSL: bool = bool(environ.get("ES_DISABLE_VERIFY_SSL"))

    def print_generic(self):
        """print generic env vars"""
        print(
            f"""
            HOST_UID: {self.HOST_UID}
            HOST_GID: {self.HOST_GID}
            TZ: {self.TZ}
            ENABLE_CAST: {self.ENABLE_CAST}
            TA_PORT: {self.TA_PORT}
            TA_UWSGI_PORT: {self.TA_UWSGI_PORT}
            TA_USERNAME: {self.TA_USERNAME}
            TA_PASSWORD: *****"""
        )

    def print_paths(self):
        """debug paths set"""
        print(
            f"""
            MEDIA_DIR: {self.MEDIA_DIR}
            APP_DIR: {self.APP_DIR}
            CACHE_DIR: {self.CACHE_DIR}"""
        )

    def print_redis_conf(self):
        """debug redis conf paths"""
        print(
            f"""
            REDIS_HOST: {self.REDIS_HOST}
            REDIS_PORT: {self.REDIS_PORT}
            REDIS_NAME_SPACE: {self.REDIS_NAME_SPACE}"""
        )

    def print_es_paths(self):
        """debug es conf"""
        print(
            f"""
            ES_URL: {self.ES_URL}
            ES_PASS: *****
            ES_USER: {self.ES_USER}
            ES_SNAPSHOT_DIR: {self.ES_SNAPSHOT_DIR}
            ES_DISABLE_VERIFY_SSL: {self.ES_DISABLE_VERIFY_SSL}"""
        )

    def print_all(self):
        """print all"""
        self.print_generic()
        self.print_paths()
        self.print_redis_conf()
        self.print_es_paths()
