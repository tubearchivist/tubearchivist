"""
ffmpeg link builder
copied as into build step in Dockerfile
"""

import json
import os
import sys
import tarfile
import urllib.request
from enum import Enum

API_URL = "https://api.github.com/repos/yt-dlp/FFmpeg-Builds/releases/latest"
BINARIES = ["ffmpeg", "ffprobe"]


class PlatformFilter(Enum):
    """options"""

    ARM64 = "linuxarm64"
    AMD64 = "linux64"


def get_assets():
    """get all available assets from latest build"""
    with urllib.request.urlopen(API_URL) as f:
        all_links = json.loads(f.read().decode("utf-8"))

    return all_links


def pick_url(all_links, platform):
    """pick url for platform"""
    filter_by = PlatformFilter[platform.split("/")[1].upper()].value
    options = [i for i in all_links["assets"] if filter_by in i["name"]]
    if not options:
        raise ValueError(f"no valid asset found for filter {filter_by}")

    url_pick = options[0]["browser_download_url"]

    return url_pick


def download_extract(url):
    """download and extract binaries"""
    print("download file")
    filename, _ = urllib.request.urlretrieve(url)
    print("extract file")
    with tarfile.open(filename, "r:xz") as tar:
        for member in tar.getmembers():
            member.name = os.path.basename(member.name)
            if member.name in BINARIES:
                print(f"extract {member.name}")
                tar.extract(member, member.name)


def main():
    """entry point"""
    args = sys.argv
    if len(args) == 1:
        platform = "linux/amd64"
    else:
        platform = args[1]

    all_links = get_assets()
    url = pick_url(all_links, platform)
    download_extract(url)


if __name__ == "__main__":
    main()
