"""
functionality:
- interact with redis
- hold temporary download queue in redis
"""

import json
import os

import redis


class RedisBase:
    """connection base for redis"""

    REDIS_HOST = os.environ.get("REDIS_HOST")
    REDIS_PORT = os.environ.get("REDIS_PORT") or 6379
    NAME_SPACE = "ta:"

    def __init__(self):
        self.conn = redis.Redis(host=self.REDIS_HOST, port=self.REDIS_PORT)


class RedisArchivist(RedisBase):
    """collection of methods to interact with redis"""

    CHANNELS = [
        "download",
        "add",
        "rescan",
        "subchannel",
        "subplaylist",
        "playlistscan",
        "setting",
    ]

    def set_message(self, key, message, expire=True):
        """write new message to redis"""
        self.conn.execute_command(
            "JSON.SET", self.NAME_SPACE + key, ".", json.dumps(message)
        )

        if expire:
            if isinstance(expire, bool):
                secs = 20
            else:
                secs = expire
            self.conn.execute_command("EXPIRE", self.NAME_SPACE + key, secs)

    def get_message(self, key):
        """get message dict from redis"""
        reply = self.conn.execute_command("JSON.GET", self.NAME_SPACE + key)
        if reply:
            json_str = json.loads(reply)
        else:
            json_str = {"status": False}

        return json_str

    def list_items(self, query):
        """list all matches"""
        reply = self.conn.execute_command(
            "KEYS", self.NAME_SPACE + query + "*"
        )
        all_matches = [i.decode().lstrip(self.NAME_SPACE) for i in reply]
        all_results = []
        for match in all_matches:
            json_str = self.get_message(match)
            all_results.append(json_str)

        return all_results

    def del_message(self, key):
        """delete key from redis"""
        response = self.conn.execute_command("DEL", self.NAME_SPACE + key)
        return response

    def get_lock(self, lock_key):
        """handle lock for task management"""
        redis_lock = self.conn.lock(self.NAME_SPACE + lock_key)
        return redis_lock

    def get_progress(self):
        """get a list of all progress messages"""
        all_messages = []
        for channel in self.CHANNELS:
            key = "message:" + channel
            reply = self.conn.execute_command(
                "JSON.GET", self.NAME_SPACE + key
            )
            if reply:
                json_str = json.loads(reply)
                all_messages.append(json_str)

        return all_messages


class RedisQueue(RedisBase):
    """dynamically interact with the download queue in redis"""

    def __init__(self):
        super().__init__()
        self.key = self.NAME_SPACE + "dl_queue"

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
