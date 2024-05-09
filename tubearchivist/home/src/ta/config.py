"""
Functionality:
- read and write config
- load config variables into redis
"""

import json
from random import randint
from time import sleep

import requests
from django.conf import settings
from home.src.ta.ta_redis import RedisArchivist


class AppConfig:
    """handle application variables"""

    def __init__(self):
        self.config = self.get_config()

    def get_config(self):
        """get config from default file or redis if changed"""
        config = self.get_config_redis()
        if not config:
            config = self.get_config_file()

        return config

    def get_config_file(self):
        """read the defaults from config.json"""
        with open("home/config.json", "r", encoding="utf-8") as f:
            config_file = json.load(f)

        return config_file

    @staticmethod
    def get_config_redis():
        """read config json set from redis to overwrite defaults"""
        for i in range(10):
            try:
                config = RedisArchivist().get_message("config")
                if not list(config.values())[0]:
                    return False

                return config

            except Exception:  # pylint: disable=broad-except
                print(f"... Redis connection failed, retry [{i}/10]")
                sleep(3)

        raise ConnectionError("failed to connect to redis")

    def update_config(self, form_post):
        """update config values from settings form"""
        updated = []
        for key, value in form_post.items():
            if not value and not isinstance(value, int):
                continue

            if value in ["0", 0]:
                to_write = False
            elif value == "1":
                to_write = True
            else:
                to_write = value

            config_dict, config_value = key.split("_", maxsplit=1)
            self.config[config_dict][config_value] = to_write
            updated.append((config_value, to_write))

        RedisArchivist().set_message("config", self.config, save=True)
        return updated

    def load_new_defaults(self):
        """check config.json for missing defaults"""
        default_config = self.get_config_file()
        redis_config = self.get_config_redis()

        # check for customizations
        if not redis_config:
            config = self.get_config()
            RedisArchivist().set_message("config", config)
            return False

        needs_update = False

        for key, value in default_config.items():
            # missing whole main key
            if key not in redis_config:
                redis_config.update({key: value})
                needs_update = True
                continue

            # missing nested values
            for sub_key, sub_value in value.items():
                if sub_key not in redis_config[key].keys():
                    redis_config[key].update({sub_key: sub_value})
                    needs_update = True

        if needs_update:
            RedisArchivist().set_message("config", redis_config)

        return needs_update


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
        message = RedisArchivist().get_message(self.NEW_KEY)
        if not message.get("status"):
            return {}

        return message
