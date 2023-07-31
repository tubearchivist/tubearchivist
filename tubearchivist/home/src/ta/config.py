"""
Functionality:
- read and write config
- load config variables into redis
"""

import json
import os
import re
from random import randint
from time import sleep

import requests
from celery.schedules import crontab
from django.conf import settings
from home.src.ta.ta_redis import RedisArchivist


class AppConfig:
    """handle user settings and application variables"""

    def __init__(self, user_id=False):
        self.user_id = user_id
        self.config = self.get_config()
        self.colors = self.get_colors()

    def get_config(self):
        """get config from default file or redis if changed"""
        config = self.get_config_redis()
        if not config:
            config = self.get_config_file()

        if self.user_id:
            key = f"{self.user_id}:page_size"
            page_size = RedisArchivist().get_message(key)["status"]
            if page_size:
                config["archive"]["page_size"] = page_size

        config["application"].update(self.get_config_env())
        return config

    def get_config_file(self):
        """read the defaults from config.json"""
        with open("home/config.json", "r", encoding="utf-8") as f:
            config_file = json.load(f)

        config_file["application"].update(self.get_config_env())

        return config_file

    @staticmethod
    def get_config_env():
        """read environment application variables"""
        es_pass = os.environ.get("ELASTIC_PASSWORD")
        es_user = os.environ.get("ELASTIC_USER", default="elastic")

        application = {
            "REDIS_HOST": os.environ.get("REDIS_HOST"),
            "es_url": os.environ.get("ES_URL"),
            "es_auth": (es_user, es_pass),
            "HOST_UID": int(os.environ.get("HOST_UID", False)),
            "HOST_GID": int(os.environ.get("HOST_GID", False)),
            "enable_cast": bool(os.environ.get("ENABLE_CAST")),
        }

        return application

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

        RedisArchivist().set_message("config", self.config)
        return updated

    @staticmethod
    def set_user_config(form_post, user_id):
        """set values in redis for user settings"""
        for key, value in form_post.items():
            if not value:
                continue

            message = {"status": value}
            redis_key = f"{user_id}:{key}"
            RedisArchivist().set_message(redis_key, message)

    def get_colors(self):
        """overwrite config if user has set custom values"""
        colors = False
        if self.user_id:
            col_dict = RedisArchivist().get_message(f"{self.user_id}:colors")
            colors = col_dict["status"]

        if not colors:
            colors = self.config["application"]["colors"]

        self.config["application"]["colors"] = colors
        return colors

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
                if sub_key not in redis_config[key].keys():
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
                        "status": self.MSG,
                        "level": "error",
                        "title": "Scheduler update failed.",
                        "message": "Invalid schedule input",
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

        RedisArchivist().set_message("config", redis_config)
        mess_dict = {
            "status": self.MSG,
            "level": "info",
            "title": "Scheduler changed.",
            "message": "Please restart container for changes to take effect",
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
        new_version, is_breaking = self._has_update()
        if new_version:
            message = {
                "status": True,
                "version": new_version,
                "is_breaking": is_breaking,
            }
            RedisArchivist().set_message(self.NEW_KEY, message)
            print(f"[{self.local_version}]: found new version {new_version}")

    def get_local_version(self):
        """read version from local"""
        return self.local_version

    def get_remote_version(self):
        """read version from remote"""
        self.response = requests.get(self.REMOTE_URL, timeout=20).json()
        remote_version_str = self.response["release_version"]
        self.remote_version = self._parse_version(remote_version_str)
        self.is_breaking = self.response["breaking_changes"]

    def _has_update(self):
        """check if there is an update"""
        for idx, number in enumerate(self.local_version):
            is_newer = self.remote_version[idx] > number
            if is_newer:
                return self.response["release_version"], self.is_breaking

        if self.is_unstable and self.local_version == self.remote_version:
            return self.response["release_version"], self.is_breaking

        return False, False

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

        if self._parse_version(message.get("version")) == self.local_version:
            RedisArchivist().del_message(self.NEW_KEY)
            return settings.TA_VERSION

        return False

    def get_update(self):
        """return new version dict if available"""
        message = RedisArchivist().get_message(self.NEW_KEY)
        if not message.get("status"):
            return False

        return message
