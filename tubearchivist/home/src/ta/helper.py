"""
Loose collection of helper functions
- don't import AppConfig class here to avoid circular imports
"""

import random
import re
import string
import subprocess
import unicodedata
from datetime import datetime
from urllib.parse import parse_qs, urlparse

import yt_dlp


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


def randomizor(length):
    """generate random alpha numeric string"""
    pool = string.digits + string.ascii_letters
    return "".join(random.choice(pool) for i in range(length))


def requests_headers():
    """build header with random user agent for requests outside of yt-dlp"""

    chrome_versions = (
        "90.0.4430.212",
        "90.0.4430.24",
        "90.0.4430.70",
        "90.0.4430.72",
        "90.0.4430.85",
        "90.0.4430.93",
        "91.0.4472.101",
        "91.0.4472.106",
        "91.0.4472.114",
        "91.0.4472.124",
        "91.0.4472.164",
        "91.0.4472.19",
        "91.0.4472.77",
        "92.0.4515.107",
        "92.0.4515.115",
        "92.0.4515.131",
        "92.0.4515.159",
        "92.0.4515.43",
        "93.0.4556.0",
        "93.0.4577.15",
        "93.0.4577.63",
        "93.0.4577.82",
        "94.0.4606.41",
        "94.0.4606.54",
        "94.0.4606.61",
        "94.0.4606.71",
        "94.0.4606.81",
        "94.0.4606.85",
        "95.0.4638.17",
        "95.0.4638.50",
        "95.0.4638.54",
        "95.0.4638.69",
        "95.0.4638.74",
        "96.0.4664.18",
        "96.0.4664.45",
        "96.0.4664.55",
        "96.0.4664.93",
        "97.0.4692.20",
    )
    template = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        + "AppleWebKit/537.36 (KHTML, like Gecko) "
        + f"Chrome/{random.choice(chrome_versions)} Safari/537.36"
    )

    return {"User-Agent": template}


def date_praser(timestamp):
    """return formatted date string"""
    if isinstance(timestamp, int):
        date_obj = datetime.fromtimestamp(timestamp)
    elif isinstance(timestamp, str):
        date_obj = datetime.strptime(timestamp, "%Y-%m-%d")

    return datetime.strftime(date_obj, "%d %b, %Y")


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
