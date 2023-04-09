"""
Loose collection of helper functions
- don't import AppConfig class here to avoid circular imports
"""

import json
import os
import random
import re
import string
import subprocess
import unicodedata
from datetime import datetime
from urllib.parse import urlparse

import requests


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


def time_parser(timestamp):
    """return seconds from timestamp, false on empty"""
    if not timestamp:
        return False

    if timestamp.isnumeric():
        return int(timestamp)

    hours, minutes, seconds = timestamp.split(":", maxsplit=3)
    return int(hours) * 60 * 60 + int(minutes) * 60 + float(seconds)


def clear_dl_cache(config):
    """clear leftover files from dl cache"""
    print("clear download cache")
    cache_dir = os.path.join(config["application"]["cache_dir"], "download")
    leftover_files = os.listdir(cache_dir)
    for cached in leftover_files:
        to_delete = os.path.join(cache_dir, cached)
        os.remove(to_delete)

    return len(leftover_files)


def get_mapping():
    """read index_mapping.json and get expected mapping and settings"""
    with open("home/src/es/index_mapping.json", "r", encoding="utf-8") as f:
        index_config = json.load(f).get("index_config")

    return index_config


def is_shorts(youtube_id):
    """check if youtube_id is a shorts video, bot not it it's not a shorts"""
    shorts_url = f"https://www.youtube.com/shorts/{youtube_id}"
    response = requests.head(
        shorts_url, headers=requests_headers(), timeout=10
    )

    return response.status_code == 200


def ta_host_parser(ta_host):
    """parse ta_host env var for ALLOWED_HOSTS and CSRF_TRUSTED_ORIGINS"""
    allowed_hosts = []
    csrf_trusted_origins = []
    for host in ta_host.split():
        host_clean = host.strip()
        if not host_clean.startswith("http"):
            host_clean = f"http://{host_clean}"

        parsed = urlparse(host_clean)
        allowed_hosts.append(f"{parsed.hostname}")
        csrf_trusted_origins.append(f"{parsed.scheme}://{parsed.hostname}")

    return allowed_hosts, csrf_trusted_origins


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
