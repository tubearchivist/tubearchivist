"""
Functionality:
- Handle manual import task
- Scan and identify media files in import folder
- Process import media files
"""

import json
import os
import re
import shutil
import subprocess

from home.src.download.thumbnails import ThumbManager
from home.src.index.comments import CommentList
from home.src.index.video import YoutubeVideo
from home.src.ta.config import AppConfig
from home.src.ta.helper import ignore_filelist
from home.src.ta.settings import EnvironmentSettings
from PIL import Image
from yt_dlp.utils import ISO639Utils


class ImportFolderScanner:
    """import and indexing existing video files
    - identify all media files belonging to a video
    - identify youtube id
    - convert if needed
    """

    CONFIG = AppConfig().config
    CACHE_DIR = EnvironmentSettings.CACHE_DIR
    IMPORT_DIR = os.path.join(CACHE_DIR, "import")

    """All extensions should be in lowercase until better handling is in place.
    Described in Issue #502.
    """
    EXT_MAP = {
        "media": [".mp4", ".mkv", ".webm"],
        "metadata": [".json"],
        "thumb": [".jpg", ".png", ".webp"],
        "subtitle": [".vtt"],
    }

    def __init__(self, task=False):
        self.task = task
        self.to_import = False

    def scan(self):
        """scan and match media files"""
        if self.task:
            self.task.send_progress(["Scanning your import folder."])

        all_files = self.get_all_files()
        self.match_files(all_files)
        self.process_videos()

        return self.to_import

    def get_all_files(self):
        """get all files in /import"""
        rel_paths = ignore_filelist(os.listdir(self.IMPORT_DIR))
        all_files = [os.path.join(self.IMPORT_DIR, i) for i in rel_paths]
        all_files.sort()

        return all_files

    @staticmethod
    def _get_template():
        """base dict for video"""
        return {
            "media": False,
            "video_id": False,
            "metadata": False,
            "thumb": False,
            "subtitle": [],
        }

    def match_files(self, all_files):
        """loop through all files, join what matches"""
        self.to_import = []

        current_video = self._get_template()
        last_base = False

        for file_path in all_files:
            base_name, ext = self._detect_base_name(file_path)
            key, file_path = self._detect_type(file_path, ext)
            if not key or not file_path:
                continue

            if base_name != last_base:
                if last_base:
                    print(f"manual import: {current_video}")
                    self.to_import.append(current_video)

                current_video = self._get_template()
                last_base = base_name

            if key == "subtitle":
                current_video["subtitle"].append(file_path)
            else:
                current_video[key] = file_path

        if current_video.get("media"):
            print(f"manual import: {current_video}")
            self.to_import.append(current_video)

    def _detect_base_name(self, file_path):
        """extract base_name and ext for matching"""
        base_name_raw, ext = os.path.splitext(file_path)
        base_name, ext2 = os.path.splitext(base_name_raw)

        if ext2:
            if ISO639Utils.short2long(ext2.strip(".")) or ext2 == ".info":
                # valid secondary extension
                return base_name, ext

        return base_name_raw, ext

    def _detect_type(self, file_path, ext):
        """detect metadata type for file"""

        for key, value in self.EXT_MAP.items():
            if ext.lower() in value:
                return key, file_path

        return False, False

    def process_videos(self):
        """loop through all videos"""
        for idx, current_video in enumerate(self.to_import):
            if not current_video["media"]:
                print(f"{current_video}: no matching media file found.")
                raise ValueError

            if self.task:
                self._notify(idx, current_video)

            self._detect_youtube_id(current_video)
            self._dump_thumb(current_video)
            self._convert_thumb(current_video)
            self._get_subtitles(current_video)
            self._convert_video(current_video)
            print(f"manual import: {current_video}")

            ManualImport(current_video, self.CONFIG).run()

        video_ids = [i["video_id"] for i in self.to_import]
        comment_list = CommentList(task=self.task)
        comment_list.add(video_ids=video_ids)
        comment_list.index()

    def _notify(self, idx, current_video):
        """send notification back to task"""
        filename = os.path.split(current_video["media"])[-1]
        if len(filename) > 50:
            filename = filename[:50] + "..."

        message = [
            f"Import queue processing video {idx + 1}/{len(self.to_import)}",
            filename,
        ]
        progress = (idx + 1) / len(self.to_import)
        self.task.send_progress(message, progress=progress)

    def _detect_youtube_id(self, current_video):
        """find video id from filename or json"""
        youtube_id = self._extract_id_from_filename(current_video["media"])
        if youtube_id:
            current_video["video_id"] = youtube_id
            return

        youtube_id = self._extract_id_from_json(current_video["metadata"])
        if youtube_id:
            current_video["video_id"] = youtube_id
            return

        raise ValueError("failed to find video id")

    @staticmethod
    def _extract_id_from_filename(file_name):
        """
        look at the file name for the youtube id
        expects filename ending in [<youtube_id>].<ext>
        """
        base_name, _ = os.path.splitext(file_name)
        id_search = re.search(r"\[([a-zA-Z0-9_-]{11})\]$", base_name)
        if id_search:
            youtube_id = id_search.group(1)
            return youtube_id

        print(f"id extraction failed from filename: {file_name}")

        return False

    def _extract_id_from_json(self, json_file):
        """open json file and extract id"""
        json_path = os.path.join(self.CACHE_DIR, "import", json_file)
        with open(json_path, "r", encoding="utf-8") as f:
            json_content = f.read()

        youtube_id = json.loads(json_content)["id"]

        return youtube_id

    def _dump_thumb(self, current_video):
        """extract embedded thumb before converting"""
        if current_video["thumb"]:
            return

        media_path = current_video["media"]
        _, ext = os.path.splitext(media_path)

        new_path = False
        if ext == ".mkv":
            idx, thumb_type = self._get_mkv_thumb_stream(media_path)
            if idx is not None:
                new_path = self.dump_mpv_thumb(media_path, idx, thumb_type)

        elif ext == ".mp4":
            thumb_type = self.get_mp4_thumb_type(media_path)
            if thumb_type:
                new_path = self.dump_mp4_thumb(media_path, thumb_type)

        if new_path:
            current_video["thumb"] = new_path

    def _get_mkv_thumb_stream(self, media_path):
        """get stream idx of thumbnail for mkv files"""
        streams = self._get_streams(media_path)
        attachments = [
            i for i in streams["streams"] if i["codec_type"] == "attachment"
        ]

        for idx, stream in enumerate(attachments):
            tags = stream["tags"]
            if "mimetype" in tags and tags["filename"].startswith("cover"):
                _, ext = os.path.splitext(tags["filename"])
                return idx, ext

        return None, None

    @staticmethod
    def dump_mpv_thumb(media_path, idx, thumb_type):
        """write cover to disk for mkv"""
        _, media_ext = os.path.splitext(media_path)
        new_path = f"{media_path.rstrip(media_ext)}{thumb_type}"
        subprocess.run(
            [
                "ffmpeg",
                "-v",
                "quiet",
                f"-dump_attachment:t:{idx}",
                new_path,
                "-i",
                media_path,
            ],
            check=False,
        )

        return new_path

    def get_mp4_thumb_type(self, media_path):
        """detect filetype of embedded thumbnail"""
        streams = self._get_streams(media_path)

        for stream in streams["streams"]:
            if stream["codec_name"] in ["png", "jpg"]:
                return stream["codec_name"]

        return False

    def _convert_thumb(self, current_video):
        """convert all thumbnails to jpg"""
        if not current_video["thumb"]:
            return

        thumb_path = current_video["thumb"]

        base_path, ext = os.path.splitext(thumb_path)
        if ext == ".jpg":
            return

        new_path = f"{base_path}.jpg"
        img_raw = Image.open(thumb_path)
        img_raw.convert("RGB").save(new_path)

        os.remove(thumb_path)
        current_video["thumb"] = new_path

    def _get_subtitles(self, current_video):
        """find all subtitles in media file"""
        if current_video["subtitle"]:
            return

        media_path = current_video["media"]
        streams = self._get_streams(media_path)
        base_path, ext = os.path.splitext(media_path)

        if ext == ".webm":
            print(f"{media_path}: subtitle extract from webm not supported")
            return

        for idx, stream in enumerate(streams["streams"]):
            if stream["codec_type"] == "subtitle":
                lang = ISO639Utils.long2short(stream["tags"]["language"])
                sub_path = f"{base_path}.{lang}.vtt"
                if sub_path in current_video["subtitle"]:
                    continue
                self._dump_subtitle(idx, media_path, sub_path)
                current_video["subtitle"].append(sub_path)

    @staticmethod
    def _dump_subtitle(idx, media_path, sub_path):
        """extract subtitle from media file"""
        subprocess.run(
            ["ffmpeg", "-i", media_path, "-map", f"0:{idx}", sub_path],
            check=True,
        )

    @staticmethod
    def _get_streams(media_path):
        """return all streams from media_path"""
        streams_raw = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_streams",
                "-print_format",
                "json",
                media_path,
            ],
            capture_output=True,
            check=True,
        )
        streams = json.loads(streams_raw.stdout.decode())

        return streams

    @staticmethod
    def dump_mp4_thumb(media_path, thumb_type):
        """save cover to disk"""
        _, ext = os.path.splitext(media_path)
        new_path = f"{media_path.rstrip(ext)}.{thumb_type}"

        subprocess.run(
            [
                "ffmpeg",
                "-i",
                media_path,
                "-map",
                "0:v",
                "-map",
                "-0:V",
                "-c",
                "copy",
                new_path,
            ],
            check=True,
        )

        return new_path

    def _convert_video(self, current_video):
        """convert if needed"""
        current_path = current_video["media"]
        base_path, ext = os.path.splitext(current_path)
        if ext == ".mp4":
            return

        new_path = base_path + ".mp4"
        subprocess.run(
            [
                "ffmpeg",
                "-i",
                current_path,
                new_path,
                "-loglevel",
                "warning",
                "-stats",
            ],
            check=True,
        )
        current_video["media"] = new_path
        os.remove(current_path)


class ManualImport:
    """import single identified video"""

    def __init__(self, current_video, config):
        self.current_video = current_video
        self.config = config

    def run(self):
        """run all"""
        json_data = self.index_metadata()
        self._move_to_archive(json_data)
        self._cleanup(json_data)

    def index_metadata(self):
        """get metadata from yt or json"""
        video_id = self.current_video["video_id"]
        video = YoutubeVideo(video_id)
        video.build_json(
            youtube_meta_overwrite=self._get_info_json(),
            media_path=self.current_video["media"],
        )
        if not video.json_data:
            print(f"{video_id}: manual import failed, and no metadata found.")
            raise ValueError

        video.check_subtitles(subtitle_files=self.current_video["subtitle"])
        video.upload_to_es()

        if video.offline_import and self.current_video["thumb"]:
            old_path = self.current_video["thumb"]
            thumbs = ThumbManager(video_id)
            new_path = thumbs.vid_thumb_path(absolute=True, create_folder=True)
            shutil.move(old_path, new_path, copy_function=shutil.copyfile)
        else:
            url = video.json_data["vid_thumb_url"]
            ThumbManager(video_id).download_video_thumb(url)

        return video.json_data

    def _get_info_json(self):
        """read info_json from file"""
        if not self.current_video["metadata"]:
            return False

        with open(self.current_video["metadata"], "r", encoding="utf-8") as f:
            info_json = json.loads(f.read())

        return info_json

    def _move_to_archive(self, json_data):
        """move identified media file to archive"""
        videos = EnvironmentSettings.MEDIA_DIR
        host_uid = EnvironmentSettings.HOST_UID
        host_gid = EnvironmentSettings.HOST_GID

        channel, file = os.path.split(json_data["media_url"])
        channel_folder = os.path.join(videos, channel)
        if not os.path.exists(channel_folder):
            os.makedirs(channel_folder)

        if host_uid and host_gid:
            os.chown(channel_folder, host_uid, host_gid)

        old_path = self.current_video["media"]
        new_path = os.path.join(channel_folder, file)
        shutil.move(old_path, new_path, copy_function=shutil.copyfile)
        if host_uid and host_gid:
            os.chown(new_path, host_uid, host_gid)

        base_name, _ = os.path.splitext(new_path)
        for old_path in self.current_video["subtitle"]:
            lang = old_path.split(".")[-2]
            new_path = f"{base_name}.{lang}.vtt"
            shutil.move(old_path, new_path, copy_function=shutil.copyfile)

    def _cleanup(self, json_data):
        """cleanup leftover files"""
        meta_data = self.current_video["metadata"]
        if meta_data and os.path.exists(meta_data):
            os.remove(meta_data)

        thumb = self.current_video["thumb"]
        if thumb and os.path.exists(thumb):
            os.remove(thumb)

        for subtitle_file in self.current_video["subtitle"]:
            if os.path.exists(subtitle_file):
                os.remove(subtitle_file)

        channel_info = os.path.join(
            EnvironmentSettings.CACHE_DIR,
            "import",
            f"{json_data['channel']['channel_id']}.info.json",
        )
        if os.path.exists(channel_info):
            os.remove(channel_info)
