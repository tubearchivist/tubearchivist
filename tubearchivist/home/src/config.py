"""
Functionality:
- read and write config
- load config variables into redis
- needs to be a separate module to avoid circular import
"""

import json
import os

from home.src.helper import get_message, set_message


class AppConfig:
    """ handle user settings and application variables """

    def __init__(self):
        self.config = self.get_config()

    def get_config(self):
        """ get config from default file or redis if changed """
        config = self.get_config_redis()
        if not config:
            with open('home/config.json', encoding="utf-8") as f:
                config_str = f.read()
                config = json.loads(config_str)

        config['application']['REDIS_HOST'] = os.environ.get('REDIS_HOST')
        config['application']['es_url'] = os.environ.get('ES_URL')
        config['application']['HOST_UID'] = int(os.environ.get('HOST_UID'))
        config['application']['HOST_GID'] = int(os.environ.get('HOST_GID'))
        return config

    @staticmethod
    def get_config_redis():
        """ read config json set from redis to overwrite defaults """
        config = get_message('config')
        if not list(config.values())[0]:
            return False

        return config

    def update_config(self, form_post):
        """ update config values from settings form """
        config = self.config
        for key, value in form_post.items():
            to_write = value[0]
            if len(to_write):
                if to_write == '0':
                    to_write = False
                elif to_write.isdigit():
                    to_write = int(to_write)

                config_dict, config_value = key.split('.')
                config[config_dict][config_value] = to_write

        with open('home/config.json', 'w', encoding="utf-8") as f:
            f.write(json.dumps(config))

        set_message('config', config, expire=False)
