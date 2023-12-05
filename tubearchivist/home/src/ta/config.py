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

    @staticmethod
    def _build_rand_daily():
        """build random daily schedule per installation"""
        return {
            "minute": randint(0, 59),
            "hour": randint(0, 23),
            "day_of_week": "*",
        }

    def load_new_defaults(self):
        """check config.json for missing defaults"""
        default_config = self.get_config_file()
        redis_config = self.get_config_redis()

        # check for customizations
        if not redis_config:
            config = self.get_config()
            config["scheduler"]["version_check"] = self._build_rand_daily()
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
                if (
                    sub_key not in redis_config[key].keys()
                    or sub_value == "rand-d"
                ):
                    if sub_value == "rand-d":
                        sub_value = self._build_rand_daily()

                    redis_config[key].update({sub_key: sub_value})
                    needs_update = True

        if needs_update:
            RedisArchivist().set_message("config", redis_config)

        return needs_update


class ReleaseVersion:
    """compare local version with remote version"""

    REMOTE_URL = "https://www.tubearchivist.com/api/release/latest/"
    NEW_KEY = "versioncheck:new"

    def __init__(self):
        self.local_version = self._parse_version(settings.TA_VERSION)
        self.is_unstable = settings.TA_VERSION.endswith("-unstable")
        self.remote_version = False
        self.is_breaking = False
        self.response = False

    def check(self):
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

    def get_local_version(self):
        """read version from local"""
        return self.local_version

    def get_remote_version(self):
        """read version from remote"""
        sleep(randint(0, 60))
        self.response = requests.get(self.REMOTE_URL, timeout=20).json()
        remote_version_str = self.response["release_version"]
        self.remote_version = self._parse_version(remote_version_str)
        self.is_breaking = self.response["breaking_changes"]

    def _has_update(self):
        """check if there is an update"""
        if self.remote_version > self.local_version:
            return self.remote_version

        if self.is_unstable and self.local_version == self.remote_version:
            return self.remote_version

        return False

    @staticmethod
    def _parse_version(version):
        """return version parts"""
        clean = version.rstrip("-unstable").lstrip("v")
        return tuple((int(i) for i in clean.split(".")))

    def is_updated(self):
        """check if update happened in the mean time"""
        message = self.get_update()
        if not message:
            return False

        if self.local_version >= self._parse_version(message.get("version")):
            RedisArchivist().del_message(self.NEW_KEY)
            return settings.TA_VERSION

        return False

    def get_update(self):
        """return new version dict if available"""
        message = RedisArchivist().get_message(self.NEW_KEY)
        if not message.get("status"):
            return False

        return message
