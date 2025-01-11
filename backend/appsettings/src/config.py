"""
Functionality:
- read and write config
- load config variables into redis
"""

from random import randint
from time import sleep
from typing import Literal, TypedDict

import requests
from appsettings.src.snapshot import ElasticSnapshot
from common.src.es_connect import ElasticWrap
from common.src.ta_redis import RedisArchivist
from django.conf import settings


class SubscriptionsConfigType(TypedDict):
    """describes subscriptions config"""

    channel_size: int
    live_channel_size: int
    shorts_channel_size: int
    auto_start: bool


class DownloadsConfigType(TypedDict):
    """describes downloads config"""

    limit_speed: int
    sleep_interval: int
    autodelete_days: int
    format: str | bool
    format_sort: str | bool
    add_metadata: bool
    add_thumbnail: bool
    subtitle: str | bool
    subtitle_source: Literal["user", "auto"] | bool
    subtitle_index: bool
    comment_max: str | bool
    comment_sort: Literal["top", "new"]
    cookie_import: bool
    throttledratelimit: int
    extractor_lang: str | bool
    integrate_ryd: bool
    integrate_sponsorblock: bool


class ApplicationConfigType(TypedDict):
    """describes application config"""

    enable_snapshot: bool


class AppConfigType(TypedDict):
    """combined app config type"""

    subscriptions: SubscriptionsConfigType
    downloads: DownloadsConfigType
    application: ApplicationConfigType


class AppConfig:
    """handle application variables"""

    ES_PATH = "ta_config/_doc/appsettings"
    CONFIG_DEFAULTS: AppConfigType = {
        "subscriptions": {
            "channel_size": 50,
            "live_channel_size": 50,
            "shorts_channel_size": 50,
            "auto_start": False,
        },
        "downloads": {
            "limit_speed": False,
            "sleep_interval": 10,
            "autodelete_days": False,
            "format": False,
            "format_sort": False,
            "add_metadata": False,
            "add_thumbnail": False,
            "subtitle": False,
            "subtitle_source": False,
            "subtitle_index": False,
            "comment_max": False,
            "comment_sort": "top",
            "cookie_import": False,
            "throttledratelimit": False,
            "extractor_lang": False,
            "integrate_ryd": False,
            "integrate_sponsorblock": False,
        },
        "application": {"enable_snapshot": True},
    }

    def __init__(self):
        self.config = self.get_config()

    def get_config(self) -> AppConfigType:
        """get config from ES"""
        response, status_code = ElasticWrap(self.ES_PATH).get()
        if not status_code == 200:
            return self.CONFIG_DEFAULTS

        return response["_source"]

    def update_config(self, data: dict) -> AppConfigType:
        """update single config value"""
        for key, value in data.items():
            key_map = key.split(".")
            self._validate_key(key_map)
            self.config[key_map[0]][key_map[1]] = value

        response, status_code = ElasticWrap(self.ES_PATH).post(self.config)
        if not status_code == 200:
            print(response)

        return self.config

    def _validate_key(self, key_map: list[str]) -> None:
        """raise valueerror on invalid key"""
        exists = self.CONFIG_DEFAULTS.get(key_map[0], {}).get(key_map[1])  # type: ignore  # noqa: E501
        if exists is None:
            raise ValueError(f"trying to access invalid config key: {key_map}")

    def post_process_updated(self, data: dict) -> None:
        """apply hooks for some config keys"""
        for config_value, updated_value in data:
            if config_value == "application.enable_snapshot" and updated_value:
                ElasticSnapshot().setup()

    @staticmethod
    def _fail_message(message_line):
        """notify our failure"""
        key = "message:setting"
        message = {
            "status": key,
            "group": "setting:application",
            "level": "error",
            "title": "Cookie import failed",
            "messages": [message_line],
            "id": "0000",
        }
        RedisArchivist().set_message(key, message=message, expire=True)


class ReleaseVersion:
    """compare local version with remote version"""

    REMOTE_URL = "https://www.tubearchivist.com/api/release/latest/"
    NEW_KEY = "versioncheck:new"

    def __init__(self) -> None:
        self.local_version: str = settings.TA_VERSION
        self.is_unstable: bool = settings.TA_VERSION.endswith("-unstable")
        self.remote_version: str = ""
        self.is_breaking: bool = False

    def check(self) -> None:
        """check version"""
        print(f"[{self.local_version}]: look for updates")
        self.get_remote_version()
        new_version = self._has_update()
        if new_version:
            message = {
                "status": True,
                "version": new_version,
                "is_breaking": self.is_breaking,
            }
            RedisArchivist().set_message(self.NEW_KEY, message)
            print(f"[{self.local_version}]: found new version {new_version}")

    def get_local_version(self) -> str:
        """read version from local"""
        return self.local_version

    def get_remote_version(self) -> None:
        """read version from remote"""
        sleep(randint(0, 60))
        response = requests.get(self.REMOTE_URL, timeout=20).json()
        self.remote_version = response["release_version"]
        self.is_breaking = response["breaking_changes"]

    def _has_update(self) -> str | bool:
        """check if there is an update"""
        remote_parsed = self._parse_version(self.remote_version)
        local_parsed = self._parse_version(self.local_version)
        if remote_parsed > local_parsed:
            return self.remote_version

        if self.is_unstable and local_parsed == remote_parsed:
            return self.remote_version

        return False

    @staticmethod
    def _parse_version(version) -> tuple[int, ...]:
        """return version parts"""
        clean = version.rstrip("-unstable").lstrip("v")
        return tuple((int(i) for i in clean.split(".")))

    def is_updated(self) -> str | bool:
        """check if update happened in the mean time"""
        message = self.get_update()
        if not message:
            return False

        local_parsed = self._parse_version(self.local_version)
        message_parsed = self._parse_version(message.get("version"))

        if local_parsed >= message_parsed:
            RedisArchivist().del_message(self.NEW_KEY)
            return settings.TA_VERSION

        return False

    def get_update(self) -> dict:
        """return new version dict if available"""
        message = RedisArchivist().get_message_dict(self.NEW_KEY)
        return message
