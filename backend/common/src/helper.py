"""
Loose collection of helper functions
- don't import AppConfig class here to avoid circular imports
"""

import json
import os
import random
import string
import subprocess
from datetime import datetime, timezone
from time import sleep
from typing import Any
from urllib.parse import urlparse

import requests
from common.src.es_connect import IndexPaginate


def ignore_filelist(filelist: list[str]) -> list[str]:
    """ignore temp files for os.listdir sanitizer"""
    to_ignore = [
        "@eaDir",
        "Icon\r\r",
        "Network Trash Folder",
        "Temporary Items",
    ]
    cleaned: list[str] = []
    for file_name in filelist:
        if file_name.startswith(".") or file_name in to_ignore:
            continue

        cleaned.append(file_name)

    return cleaned


def randomizor(length: int) -> str:
    """generate random alpha numeric string"""
    pool: str = string.digits + string.ascii_letters
    return "".join(random.choice(pool) for i in range(length))


def rand_sleep(config) -> None:
    """randomized sleep based on config"""
    sleep_config = config["downloads"].get("sleep_interval")
    if not sleep_config:
        return

    secs = random.randrange(int(sleep_config * 0.5), int(sleep_config * 1.5))
    sleep(secs)


def requests_headers() -> dict[str, str]:
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


def date_parser(timestamp: int | str | None) -> str | None:
    """return formatted date string"""
    if timestamp is None:
        return None

    if isinstance(timestamp, int):
        date_obj = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    elif isinstance(timestamp, str):
        date_obj = datetime.strptime(timestamp, "%Y-%m-%d")
        date_obj = date_obj.replace(tzinfo=timezone.utc)
    else:
        raise TypeError(f"invalid timestamp: {timestamp}")

    return date_obj.isoformat()


def time_parser(timestamp: str) -> float:
    """return seconds from timestamp, false on empty"""
    if not timestamp:
        return False

    if timestamp.isnumeric():
        return int(timestamp)

    hours, minutes, seconds = timestamp.split(":", maxsplit=3)
    return int(hours) * 60 * 60 + int(minutes) * 60 + float(seconds)


def clear_dl_cache(cache_dir: str) -> int:
    """clear leftover files from dl cache"""
    print("clear download cache")
    download_cache_dir = os.path.join(cache_dir, "download")
    leftover_files = ignore_filelist(os.listdir(download_cache_dir))
    for cached in leftover_files:
        to_delete = os.path.join(download_cache_dir, cached)
        os.remove(to_delete)

    return len(leftover_files)


def get_mapping() -> dict:
    """read index_mapping.json and get expected mapping and settings"""
    with open("appsettings/index_mapping.json", "r", encoding="utf-8") as f:
        index_config: dict = json.load(f).get("index_config")

    return index_config


def is_shorts(youtube_id: str) -> bool:
    """check if youtube_id is a shorts video, bot not it it's not a shorts"""
    shorts_url = f"https://www.youtube.com/shorts/{youtube_id}"
    cookies = {"SOCS": "CAI"}
    try:
        response = requests.head(
            shorts_url, cookies=cookies, headers=requests_headers(), timeout=10
        )
    except requests.exceptions.RequestException:
        # assume video on error
        return False

    return response.status_code == 200


def get_duration_sec(file_path: str) -> int:
    """get duration of media file from file path"""

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


def get_duration_str(seconds: int | float) -> str:
    """Return a human-readable duration string from seconds."""
    if not seconds:
        return "NA"

    seconds = int(seconds)
    units = [("y", 31536000), ("d", 86400), ("h", 3600), ("m", 60), ("s", 1)]
    duration_parts = []

    for unit_label, unit_seconds in units:
        if seconds >= unit_seconds:
            unit_count, seconds = divmod(seconds, unit_seconds)
            duration_parts.append(f"{unit_count:02}{unit_label}")

    duration_parts[0] = duration_parts[0].lstrip("0")

    return " ".join(duration_parts)


def ta_host_parser(ta_host: str) -> tuple[list[str], list[str]]:
    """parse ta_host env var for ALLOWED_HOSTS and CSRF_TRUSTED_ORIGINS"""
    allowed_hosts: list[str] = [
        "localhost",
        "tubearchivist",
    ]
    csrf_trusted_origins: list[str] = [
        "http://localhost",
        "http://tubearchivist",
    ]
    for host in ta_host.split():
        host_clean = host.strip()
        if not host_clean.startswith("http"):
            host_clean = f"http://{host_clean}"

        parsed = urlparse(host_clean)
        allowed_hosts.append(f"{parsed.hostname}")
        cors_url = f"{parsed.scheme}://{parsed.hostname}"

        if parsed.port:
            cors_url = f"{cors_url}:{parsed.port}"

        csrf_trusted_origins.append(cors_url)

    return allowed_hosts, csrf_trusted_origins


def get_stylesheets() -> list:
    """Get all valid stylesheets from /static/css"""

    stylesheets = [
        "dark.css",
        "light.css",
        "matrix.css",
        "midnight.css",
        "custom.css",
    ]
    return stylesheets


def check_stylesheet(stylesheet: str):
    """Check if a stylesheet exists. Return dark.css as a fallback"""
    if stylesheet in get_stylesheets():
        return stylesheet

    return "dark.css"


def is_missing(
    to_check: str | list[str],
    index_name: str = "ta_video,ta_download",
    on_key: str = "youtube_id",
) -> list[str]:
    """id or list of ids that are missing from index_name"""
    if isinstance(to_check, str):
        to_check = [to_check]

    data = {
        "query": {"terms": {on_key: to_check}},
        "_source": [on_key],
    }
    result = IndexPaginate(index_name, data=data).get_results()
    existing_ids = [i[on_key] for i in result]
    dl = [i for i in to_check if i not in existing_ids]

    return dl


def get_channel_overwrites() -> dict[str, dict[str, Any]]:
    """get overwrites indexed my channel_id"""
    data = {
        "query": {
            "bool": {"must": [{"exists": {"field": "channel_overwrites"}}]}
        },
        "_source": ["channel_id", "channel_overwrites"],
    }
    result = IndexPaginate("ta_channel", data).get_results()
    overwrites = {i["channel_id"]: i["channel_overwrites"] for i in result}

    return overwrites


def get_channels(
    subscribed_only: bool, source: list[str] | None = None
) -> list[dict]:
    """get a list of all channels"""
    data = {
        "sort": [{"channel_name.keyword": {"order": "asc"}}],
    }
    if subscribed_only:
        query = {"term": {"channel_subscribed": {"value": True}}}
    else:
        query = {"match_all": {}}

    data["query"] = query  # type: ignore

    if source:
        data["_source"] = source  # type: ignore

    all_channels = IndexPaginate("ta_channel", data).get_results()

    return all_channels


def get_playlists(
    subscribed_only: bool, source: list[str] | None = None
) -> list[dict]:
    """get list of playlists"""

    data = {
        "sort": [{"playlist_channel.keyword": {"order": "desc"}}],
    }

    must_list = [{"term": {"playlist_active": {"value": True}}}]
    if subscribed_only:
        must_list.append({"term": {"playlist_subscribed": {"value": True}}})

    data = {"query": {"bool": {"must": must_list}}}  # type: ignore
    if source:
        data["_source"] = source  # type: ignore

    all_playlists = IndexPaginate("ta_playlist", data).get_results()

    return all_playlists


def calc_is_watched(duration: float, position: float) -> bool:
    """considered watched based on duration position"""

    if not duration or duration <= 0:
        return False

    if duration < 60:
        threshold = 0.5
    elif duration > 900:
        threshold = 1 - (180 / duration)
    else:
        threshold = 0.9

    return position >= duration * threshold
