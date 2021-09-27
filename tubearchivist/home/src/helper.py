"""
Loose collection of helper functions
- don't import AppConfig class here to avoid circular imports
"""

import json
import os
import re
import string
import subprocess
import unicodedata

import redis
import requests

REDIS_HOST = os.environ.get("REDIS_HOST")


def get_total_hits(index, es_url, match_field):
    """get total hits from index"""
    headers = {"Content-type": "application/json"}
    data = {"query": {"match": {match_field: True}}}
    payload = json.dumps(data)
    url = f"{es_url}/{index}/_search?filter_path=hits.total"
    request = requests.post(url, data=payload, headers=headers)
    if not request.ok:
        print(request.text)
    total_json = json.loads(request.text)
    total_hits = total_json["hits"]["total"]["value"]
    return total_hits


def clean_string(file_name):
    """clean string to only asci characters"""
    whitelist = "-_.() " + string.ascii_letters + string.digits
    normalized = unicodedata.normalize("NFKD", file_name)
    ascii_only = normalized.encode("ASCII", "ignore").decode().strip()
    white_listed = "".join(c for c in ascii_only if c in whitelist)
    cleaned = re.sub(r"[ ]{2,}", " ", white_listed)
    return cleaned


def ignore_filelist(filelist):
    """ignore temp files for os.listdir sanitizer"""
    to_ignore = ["Icon\r\r", "Temporary Items", "Network Trash Folder"]
    cleaned = []
    for file_name in filelist:
        if file_name.startswith(".") or file_name in to_ignore:
            continue

        cleaned.append(file_name)

    return cleaned


def process_url_list(url_str):
    """parse url_list to find valid youtube video or channel ids"""
    to_replace = ["watch?v=", "playlist?list="]
    url_list = re.split("\n+", url_str[0])
    youtube_ids = []
    for url in url_list:
        if "/c/" in url or "/user/" in url:
            raise ValueError("user name is not unique, use channel ID")

        url_clean = url.strip().strip("/").split("/")[-1]
        for i in to_replace:
            url_clean = url_clean.replace(i, "")
        url_no_param = url_clean.split("&")[0]
        str_len = len(url_no_param)
        if str_len == 11:
            link_type = "video"
        elif str_len == 24:
            link_type = "channel"
        elif str_len == 34:
            link_type = "playlist"
        else:
            # unable to parse
            raise ValueError("not a valid url: " + url)

        youtube_ids.append({"url": url_no_param, "type": link_type})

    return youtube_ids


def set_message(key, message, expire=True):
    """write new message to redis"""
    redis_connection = redis.Redis(host=REDIS_HOST)
    redis_connection.execute_command("JSON.SET", key, ".", json.dumps(message))
    if expire:
        redis_connection.execute_command("EXPIRE", key, 20)


def get_message(key):
    """get any message from JSON key"""
    redis_connection = redis.Redis(host=REDIS_HOST)
    reply = redis_connection.execute_command("JSON.GET", key)
    if reply:
        json_str = json.loads(reply)
    else:
        json_str = {"status": False}
    return json_str


def del_message(key):
    """delete key from redis"""
    redis_connection = redis.Redis(host=REDIS_HOST)
    response = redis_connection.execute_command("DEL", key)
    return response


def get_dl_message(cache_dir):
    """get latest message if available"""
    redis_connection = redis.Redis(host=REDIS_HOST)
    reply = redis_connection.execute_command("JSON.GET", "progress:download")
    if reply:
        json_str = json.loads(reply)
    elif json_str := monitor_cache_dir(cache_dir):
        json_str = monitor_cache_dir(cache_dir)
    else:
        json_str = {"status": False}
    return json_str


def get_lock(lock_key):
    """handle lock for task management"""
    redis_lock = redis.Redis(host=REDIS_HOST).lock(lock_key)
    return redis_lock


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
            "status": "downloading",
            "level": "info",
            "title": "Downloading: " + filename,
            "message": "",
        }
    else:
        return False

    return mess_dict


class RedisQueue:
    """dynamically interact with the download queue in redis"""

    def __init__(self, key):
        self.key = key
        self.conn = redis.Redis(host=REDIS_HOST)

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


class DurationConverter:
    """
    using ffmpeg to get and parse duration from filepath
    """

    @staticmethod
    def get_sec(file_path):
        """read duration from file"""
        duration = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                file_path,
            ],
            capture_output=True,
            check=True,
        )
        duration_sec = int(float(duration.stdout.decode().strip()))
        return duration_sec

    @staticmethod
    def get_str(duration_sec):
        """takes duration in sec and returns clean string"""
        hours = duration_sec // 3600
        minutes = (duration_sec - (hours * 3600)) // 60
        secs = duration_sec - (hours * 3600) - (minutes * 60)

        duration_str = str()
        if hours:
            duration_str = str(hours).zfill(2) + ":"
        if minutes:
            duration_str = duration_str + str(minutes).zfill(2) + ":"
        else:
            duration_str = duration_str + "00:"
        duration_str = duration_str + str(secs).zfill(2)
        return duration_str
