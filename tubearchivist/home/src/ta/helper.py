"""
Loose collection of helper functions
- don't import AppConfig class here to avoid circular imports
"""

import json
import re
import string
import subprocess
import unicodedata
from urllib.parse import parse_qs, urlparse

import requests
import yt_dlp


def get_total_hits(index, es_url, es_auth, match_field):
    """get total hits from index"""
    headers = {"Content-type": "application/json"}
    data = {"query": {"match": {match_field: True}}}
    payload = json.dumps(data)
    url = f"{es_url}/{index}/_search?filter_path=hits.total"
    request = requests.post(url, data=payload, headers=headers, auth=es_auth)
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


class UrlListParser:
    """take a multi line string and detect valid youtube ids"""

    def __init__(self, url_str):
        self.url_list = [i.strip() for i in url_str.split()]

    def process_list(self):
        """loop through the list"""
        youtube_ids = []
        for url in self.url_list:
            parsed = urlparse(url)
            print(f"processing: {url}")
            print(parsed)
            if not parsed.netloc:
                # is not a url
                id_type = self.find_valid_id(url)
                youtube_id = url
            elif "youtube.com" not in url and "youtu.be" not in url:
                raise ValueError(f"{url} is not a youtube link")
            elif parsed.path:
                # is a url
                youtube_id, id_type = self.detect_from_url(parsed)
            else:
                # not detected
                raise ValueError(f"failed to detect {url}")

            youtube_ids.append({"url": youtube_id, "type": id_type})

        return youtube_ids

    def detect_from_url(self, parsed):
        """detect from parsed url"""
        if parsed.netloc == "youtu.be":
            # shortened
            youtube_id = parsed.path.strip("/")
            _ = self.find_valid_id(youtube_id)
            return youtube_id, "video"

        if parsed.query:
            # detect from query string
            query_parsed = parse_qs(parsed.query)
            if "v" in query_parsed.keys():
                youtube_id = query_parsed["v"][0]
                _ = self.find_valid_id(youtube_id)
                return youtube_id, "video"

            if "list" in query_parsed.keys():
                youtube_id = query_parsed["list"][0]
                return youtube_id, "playlist"

        if parsed.path.startswith("/channel/"):
            # channel id in url
            youtube_id = parsed.path.split("/")[2]
            _ = self.find_valid_id(youtube_id)
            return youtube_id, "channel"

        # dedect channel with yt_dlp
        youtube_id = self.extract_channel_name(parsed.geturl())
        return youtube_id, "channel"

    @staticmethod
    def find_valid_id(id_str):
        """dedect valid id from length of string"""
        str_len = len(id_str)
        if str_len == 11:
            id_type = "video"
        elif str_len == 24:
            id_type = "channel"
        elif str_len in [34, 18]:
            id_type = "playlist"
        else:
            # unable to parse
            raise ValueError("not a valid id_str: " + id_str)

        return id_type

    @staticmethod
    def extract_channel_name(url):
        """find channel id from channel name with yt-dlp help"""
        obs = {
            "default_search": "ytsearch",
            "quiet": True,
            "skip_download": True,
            "extract_flat": True,
            "playlistend": 0,
        }
        url_info = yt_dlp.YoutubeDL(obs).extract_info(url, download=False)
        try:
            channel_id = url_info["channel_id"]
        except KeyError as error:
            print(f"failed to extract channel id from {url}")
            raise ValueError from error

        return channel_id


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
        duration_raw = duration.stdout.decode().strip()
        if duration_raw == "N/A":
            return 0

        duration_sec = int(float(duration_raw))
        return duration_sec

    @staticmethod
    def get_str(duration_sec):
        """takes duration in sec and returns clean string"""
        if not duration_sec:
            # failed to extract
            return "NA"

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
