"""
Functionality:
- reindexing old documents
- syncing updated values between indexes
- scan the filesystem to delete or index
"""

import json
import os
import re
import shutil
import subprocess

from home.src.download.queue import PendingList
from home.src.download.thumbnails import ThumbManager
from home.src.es.connect import ElasticWrap
from home.src.index.video import YoutubeVideo, index_new_video
from home.src.ta.config import AppConfig
from home.src.ta.helper import clean_string, ignore_filelist
from PIL import Image, ImageFile
from yt_dlp.utils import ISO639Utils

ImageFile.LOAD_TRUNCATED_IMAGES = True


class FilesystemScanner:
    """handle scanning and fixing from filesystem"""

    CONFIG = AppConfig().config
    VIDEOS = CONFIG["application"]["videos"]

    def __init__(self):
        self.all_downloaded = self.get_all_downloaded()
        self.all_indexed = self.get_all_indexed()
        self.mismatch = None
        self.to_rename = None
        self.to_index = None
        self.to_delete = None

    def get_all_downloaded(self):
        """get a list of all video files downloaded"""
        channels = os.listdir(self.VIDEOS)
        all_channels = ignore_filelist(channels)
        all_channels.sort()
        all_downloaded = []
        for channel_name in all_channels:
            channel_path = os.path.join(self.VIDEOS, channel_name)
            channel_files = os.listdir(channel_path)
            channel_files_clean = ignore_filelist(channel_files)
            all_videos = [i for i in channel_files_clean if i.endswith(".mp4")]
            for video in all_videos:
                youtube_id = video[9:20]
                all_downloaded.append((channel_name, video, youtube_id))

        return all_downloaded

    @staticmethod
    def get_all_indexed():
        """get a list of all indexed videos"""
        index_handler = PendingList()
        index_handler.get_download()
        index_handler.get_indexed()

        all_indexed = []
        for video in index_handler.all_videos:
            youtube_id = video["youtube_id"]
            media_url = video["media_url"]
            published = video["published"]
            title = video["title"]
            all_indexed.append((youtube_id, media_url, published, title))
        return all_indexed

    def list_comarison(self):
        """compare the lists to figure out what to do"""
        self.find_unindexed()
        self.find_missing()
        self.find_bad_media_url()

    def find_unindexed(self):
        """find video files without a matching document indexed"""
        all_indexed_ids = [i[0] for i in self.all_indexed]
        to_index = []
        for downloaded in self.all_downloaded:
            if downloaded[2] not in all_indexed_ids:
                to_index.append(downloaded)

        self.to_index = to_index

    def find_missing(self):
        """find indexed videos without matching media file"""
        all_downloaded_ids = [i[2] for i in self.all_downloaded]
        to_delete = []
        for video in self.all_indexed:
            youtube_id = video[0]
            if youtube_id not in all_downloaded_ids:
                to_delete.append(video)

        self.to_delete = to_delete

    def find_bad_media_url(self):
        """rename media files not matching the indexed title"""
        to_fix = []
        to_rename = []
        for downloaded in self.all_downloaded:
            channel, filename, downloaded_id = downloaded
            # find in indexed
            for indexed in self.all_indexed:
                indexed_id, media_url, published, title = indexed
                if indexed_id == downloaded_id:
                    # found it
                    title_c = clean_string(title)
                    pub = published.replace("-", "")
                    expected_filename = f"{pub}_{indexed_id}_{title_c}.mp4"
                    new_url = os.path.join(channel, expected_filename)
                    if expected_filename != filename:
                        # file to rename
                        to_rename.append(
                            (channel, filename, expected_filename)
                        )
                    if media_url != new_url:
                        # media_url to update in es
                        to_fix.append((indexed_id, new_url))

                    break

        self.mismatch = to_fix
        self.to_rename = to_rename

    def rename_files(self):
        """rename media files as identified by find_bad_media_url"""
        for bad_filename in self.to_rename:
            channel, filename, expected_filename = bad_filename
            print(f"renaming [{filename}] to [{expected_filename}]")
            old_path = os.path.join(self.VIDEOS, channel, filename)
            new_path = os.path.join(self.VIDEOS, channel, expected_filename)
            os.rename(old_path, new_path)

    def send_mismatch_bulk(self):
        """build bulk update"""
        bulk_list = []
        for video_mismatch in self.mismatch:
            youtube_id, media_url = video_mismatch
            print(f"{youtube_id}: fixing media url {media_url}")
            action = {"update": {"_id": youtube_id, "_index": "ta_video"}}
            source = {"doc": {"media_url": media_url}}
            bulk_list.append(json.dumps(action))
            bulk_list.append(json.dumps(source))
        # add last newline
        bulk_list.append("\n")
        data = "\n".join(bulk_list)
        _, _ = ElasticWrap("_bulk").post(data=data, ndjson=True)

    def delete_from_index(self):
        """find indexed but deleted mediafile"""
        for indexed in self.to_delete:
            youtube_id = indexed[0]
            print(f"deleting {youtube_id} from index")
            path = f"ta_video/_doc/{youtube_id}"
            _, _ = ElasticWrap(path).delete()


class ImportFolderScanner:
    """import and indexing existing video files
    - identify all media files belonging to a video
    - identify youtube id
    - convert if needed
    """

    CONFIG = AppConfig().config
    CACHE_DIR = CONFIG["application"]["cache_dir"]
    IMPORT_DIR = os.path.join(CACHE_DIR, "import")

    EXT_MAP = {
        "media": [".mp4", ".mkv", ".webm"],
        "metadata": [".json"],
        "thumb": [".jpg", ".png", ".webp"],
        "subtitle": [".vtt"],
    }

    def __init__(self):
        self.to_import = False

    def scan(self):
        """scan and match media files"""
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
            if ext in value:
                return key, file_path

        return False, False

    def process_videos(self):
        """loop through all videos"""
        for current_video in self.to_import:
            if not current_video["media"]:
                print(f"{current_video}: no matching media file found.")
                raise ValueError

            self._detect_youtube_id(current_video)
            self._dump_thumb(current_video)
            self._convert_thumb(current_video)
            self._get_subtitles(current_video)
            self._convert_video(current_video)
            print(f"manual import: {current_video}")

            ManualImport(current_video, self.CONFIG).run()

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
        videos = self.config["application"]["videos"]

        channel, file = os.path.split(json_data["media_url"])
        channel_folder = os.path.join(videos, channel)
        if not os.path.exists(channel_folder):
            os.makedirs(channel_folder)

        old_path = self.current_video["media"]
        new_path = os.path.join(channel_folder, file)
        shutil.move(old_path, new_path, copy_function=shutil.copyfile)

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
            self.config["application"]["cache_dir"],
            "import",
            f"{json_data['channel']['channel_id']}.info.json",
        )
        if os.path.exists(channel_info):
            os.remove(channel_info)


def scan_filesystem():
    """grouped function to delete and update index"""
    filesystem_handler = FilesystemScanner()
    filesystem_handler.list_comarison()
    if filesystem_handler.to_rename:
        print("renaming files")
        filesystem_handler.rename_files()
    if filesystem_handler.mismatch:
        print("fixing media urls in index")
        filesystem_handler.send_mismatch_bulk()
    if filesystem_handler.to_delete:
        print("delete metadata from index")
        filesystem_handler.delete_from_index()
    if filesystem_handler.to_index:
        print("index new videos")
        for missing_vid in filesystem_handler.to_index:
            youtube_id = missing_vid[2]
            index_new_video(youtube_id)
