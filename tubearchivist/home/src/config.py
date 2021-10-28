"""
Functionality:
- read and write config
- load config variables into redis
- needs to be a separate module to avoid circular import
"""

import json
import os

from home.src.helper import RedisArchivist


class AppConfig:
    """handle user settings and application variables"""

    def __init__(self):
        self.config = self.get_config()

    def get_config(self):
        """get config from default file or redis if changed"""
        config = self.get_config_redis()
        if not config:
            config = self.get_config_file()

        config["application"].update(self.get_config_env())
        return config

    def get_config_file(self):
        """read the defaults from config.json"""
        with open("home/config.json", "r", encoding="utf-8") as f:
            config_str = f.read()
            config_file = json.loads(config_str)

        config_file["application"].update(self.get_config_env())

        return config_file

    @staticmethod
    def get_config_env():
        """read environment application variables"""
        host_uid_env = os.environ.get("HOST_UID")
        if host_uid_env:
            host_uid = int(host_uid_env)
        else:
            host_uid = False

        host_gid_env = os.environ.get("HOST_GID")
        if host_gid_env:
            host_gid = int(host_gid_env)
        else:
            host_gid = False

        es_pass = os.environ.get("ELASTIC_PASSWORD")
        es_user = os.environ.get("ELASTIC_USER", default="elastic")

        application = {
            "REDIS_HOST": os.environ.get("REDIS_HOST"),
            "es_url": os.environ.get("ES_URL"),
            "es_auth": (es_user, es_pass),
            "HOST_UID": host_uid,
            "HOST_GID": host_gid,
        }

        return application

    @staticmethod
    def get_config_redis():
        """read config json set from redis to overwrite defaults"""
        config = RedisArchivist().get_message("config")
        if not list(config.values())[0]:
            return False

        return config

    def update_config(self, form_post):
        """update config values from settings form"""
        config = self.config
        for key, value in form_post.items():
            to_write = value[0]
            if len(to_write):
                if to_write == "0":
                    to_write = False
                elif to_write == "1":
                    to_write = True
                elif to_write.isdigit():
                    to_write = int(to_write)

                config_dict, config_value = key.split(".")
                config[config_dict][config_value] = to_write

        RedisArchivist().set_message("config", config, expire=False)

    def load_new_defaults(self):
        """check config.json for missing defaults"""
        default_config = self.get_config_file()
        redis_config = self.get_config_redis()

        # check for customizations
        if not redis_config:
            return

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
            RedisArchivist().set_message("config", redis_config, expire=False)
