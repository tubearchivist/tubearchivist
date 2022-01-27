"""
functionality:
- interact with redis
- hold temporary download queue in redis
"""

import json
import os

import redis
from home.src.ta.helper import ignore_filelist


class RedisArchivist:
    """collection of methods to interact with redis"""

    REDIS_HOST = os.environ.get("REDIS_HOST")
    REDIS_PORT = os.environ.get("REDIS_PORT") or 6379
    NAME_SPACE = "ta:"
    CHANNELS = [
        "download",
        "add",
        "rescan",
        "subchannel",
        "subplaylist",
        "playlistscan",
        "setting",
    ]

    def __init__(self):
        self.redis_connection = redis.Redis(
            host=self.REDIS_HOST, port=self.REDIS_PORT
        )

    def set_message(self, key, message, expire=True):
        """write new message to redis"""
        self.redis_connection.execute_command(
            "JSON.SET", self.NAME_SPACE + key, ".", json.dumps(message)
        )

        if expire:
            if isinstance(expire, bool):
                secs = 20
            else:
                secs = expire
            self.redis_connection.execute_command(
                "EXPIRE", self.NAME_SPACE + key, secs
            )

    def get_message(self, key):
        """get message dict from redis"""
        reply = self.redis_connection.execute_command(
            "JSON.GET", self.NAME_SPACE + key
        )
        if reply:
            json_str = json.loads(reply)
        else:
            json_str = {"status": False}

        return json_str

    def del_message(self, key):
        """delete key from redis"""
        response = self.redis_connection.execute_command(
            "DEL", self.NAME_SPACE + key
        )
        return response

    def get_lock(self, lock_key):
        """handle lock for task management"""
        redis_lock = self.redis_connection.lock(self.NAME_SPACE + lock_key)
        return redis_lock

    def get_progress(self):
        """get a list of all progress messages"""
        all_messages = []
        for channel in self.CHANNELS:
            key = "message:" + channel
            reply = self.redis_connection.execute_command(
                "JSON.GET", self.NAME_SPACE + key
            )
            if reply:
                json_str = json.loads(reply)
                all_messages.append(json_str)

        return all_messages

    @staticmethod
    def monitor_cache_dir(cache_dir):
        """
        look at download cache dir directly as alternative progress info
        """
        dl_cache = os.path.join(cache_dir, "download")
        all_cache_file = os.listdir(dl_cache)
        cache_file = ignore_filelist(all_cache_file)
        if cache_file:
            filename = cache_file[0][12:].replace("_", " ").split(".")[0]
            mess_dict = {
                "status": "message:download",
                "level": "info",
                "title": "Downloading: " + filename,
                "message": "",
            }
        else:
            return False

        return mess_dict


class RedisQueue:
    """dynamically interact with the download queue in redis"""

    REDIS_HOST = os.environ.get("REDIS_HOST")
    REDIS_PORT = os.environ.get("REDIS_PORT")
    NAME_SPACE = "ta:"

    if not REDIS_PORT:
        REDIS_PORT = 6379

    def __init__(self, key):
        self.key = self.NAME_SPACE + key
        self.conn = redis.Redis(host=self.REDIS_HOST, port=self.REDIS_PORT)

    def get_all(self):
        """return all elements in list"""
        result = self.conn.execute_command("LRANGE", self.key, 0, -1)
        all_elements = [i.decode() for i in result]
        return all_elements

    def add_list(self, to_add):
        """add list to queue"""
        self.conn.execute_command("RPUSH", self.key, *to_add)

    def add_priority(self, to_add):
        """add single video to front of queue"""
        self.clear_item(to_add)
        self.conn.execute_command("LPUSH", self.key, to_add)

    def get_next(self):
        """return next element in the queue, False if none"""
        result = self.conn.execute_command("LPOP", self.key)
        if not result:
            return False

        next_element = result.decode()
        return next_element

    def clear(self):
        """delete list from redis"""
        self.conn.execute_command("DEL", self.key)

    def clear_item(self, to_clear):
        """remove single item from list if it's there"""
        self.conn.execute_command("LREM", self.key, 0, to_clear)

    def trim(self, size):
        """trim the queue based on settings amount"""
        self.conn.execute_command("LTRIM", self.key, 0, size)
