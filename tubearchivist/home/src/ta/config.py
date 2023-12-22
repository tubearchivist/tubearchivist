"""
Functionality:
- read and write config
- load config variables into redis
"""

import json
import re
from random import randint
from time import sleep

import requests
from celery.schedules import crontab
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


class ScheduleBuilder:
    """build schedule dicts for beat"""

    SCHEDULES = {
        "update_subscribed": "0 8 *",
        "download_pending": "0 16 *",
        "check_reindex": "0 12 *",
        "thumbnail_check": "0 17 *",
        "run_backup": "0 18 0",
        "version_check": "0 11 *",
    }
    CONFIG = ["check_reindex_days", "run_backup_rotate"]
    NOTIFY = [
        "update_subscribed_notify",
        "download_pending_notify",
        "check_reindex_notify",
    ]
    MSG = "message:setting"

    def __init__(self):
        self.config = AppConfig().config

    def update_schedule_conf(self, form_post):
        """process form post"""
        print("processing form, restart container for changes to take effect")
        redis_config = self.config
        for key, value in form_post.items():
            if key in self.SCHEDULES and value:
                try:
                    to_write = self.value_builder(key, value)
                except ValueError:
                    print(f"failed: {key} {value}")
                    mess_dict = {
                        "group": "setting:schedule",
                        "level": "error",
                        "title": "Scheduler update failed.",
                        "messages": ["Invalid schedule input"],
                        "id": "0000",
                    }
                    RedisArchivist().set_message(
                        self.MSG, mess_dict, expire=True
                    )
                    return

                redis_config["scheduler"][key] = to_write
            if key in self.CONFIG and value:
                redis_config["scheduler"][key] = int(value)
            if key in self.NOTIFY and value:
                if value == "0":
                    to_write = False
                else:
                    to_write = value
                redis_config["scheduler"][key] = to_write

        RedisArchivist().set_message("config", redis_config, save=True)
        mess_dict = {
            "group": "setting:schedule",
            "level": "info",
            "title": "Scheduler changed.",
            "messages": ["Restart container for changes to take effect"],
            "id": "0000",
        }
        RedisArchivist().set_message(self.MSG, mess_dict, expire=True)

    def value_builder(self, key, value):
        """validate single cron form entry and return cron dict"""
        print(f"change schedule for {key} to {value}")
        if value == "0":
            # deactivate this schedule
            return False
        if re.search(r"[\d]{1,2}\/[\d]{1,2}", value):
            # number/number cron format will fail in celery
            print("number/number schedule formatting not supported")
            raise ValueError

        keys = ["minute", "hour", "day_of_week"]
        if value == "auto":
            # set to sensible default
            values = self.SCHEDULES[key].split()
        else:
            values = value.split()

        if len(keys) != len(values):
            print(f"failed to parse {value} for {key}")
            raise ValueError("invalid input")

        to_write = dict(zip(keys, values))
        self._validate_cron(to_write)

        return to_write

    @staticmethod
    def _validate_cron(to_write):
        """validate all fields, raise value error for impossible schedule"""
        all_hours = list(re.split(r"\D+", to_write["hour"]))
        for hour in all_hours:
            if hour.isdigit() and int(hour) > 23:
                print("hour can not be greater than 23")
                raise ValueError("invalid input")

        all_days = list(re.split(r"\D+", to_write["day_of_week"]))
        for day in all_days:
            if day.isdigit() and int(day) > 6:
                print("day can not be greater than 6")
                raise ValueError("invalid input")

        if not to_write["minute"].isdigit():
            print("too frequent: only number in minutes are supported")
            raise ValueError("invalid input")

        if int(to_write["minute"]) > 59:
            print("minutes can not be greater than 59")
            raise ValueError("invalid input")

    def build_schedule(self):
        """build schedule dict as expected by app.conf.beat_schedule"""
        AppConfig().load_new_defaults()
        self.config = AppConfig().config
        schedule_dict = {}

        for schedule_item in self.SCHEDULES:
            item_conf = self.config["scheduler"][schedule_item]
            if not item_conf:
                continue

            schedule_dict.update(
                {
                    f"schedule_{schedule_item}": {
                        "task": schedule_item,
                        "schedule": crontab(
                            minute=item_conf["minute"],
                            hour=item_conf["hour"],
                            day_of_week=item_conf["day_of_week"],
                        ),
                    }
                }
            )

        return schedule_dict


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

    def clear_fail(self) -> None:
        """clear key, catch previous error in v0.4.5"""
        message = self.get_update()
        if not message:
            return

        if isinstance(message.get("version"), list):
            RedisArchivist().del_message(self.NEW_KEY)
