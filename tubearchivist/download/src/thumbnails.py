"""
functionality:
- handle download and caching for thumbnails
- check for missing thumbnails
"""

import base64
import os
from io import BytesIO
from time import sleep

import requests
from home.src.es.connect import ElasticWrap, IndexPaginate
from home.src.ta.helper import is_missing
from home.src.ta.settings import EnvironmentSettings
from mutagen.mp4 import MP4, MP4Cover
from PIL import Image, ImageFile, ImageFilter, UnidentifiedImageError

ImageFile.LOAD_TRUNCATED_IMAGES = True


class ThumbManagerBase:
    """base class for thumbnail management"""

    CACHE_DIR = EnvironmentSettings.CACHE_DIR
    VIDEO_DIR = os.path.join(CACHE_DIR, "videos")
    CHANNEL_DIR = os.path.join(CACHE_DIR, "channels")
    PLAYLIST_DIR = os.path.join(CACHE_DIR, "playlists")

    def __init__(self, item_id, item_type, fallback=False):
        self.item_id = item_id
        self.item_type = item_type
        self.fallback = fallback

    def download_raw(self, url):
        """download thumbnail for video"""
        if not url:
            return self.get_fallback()

        for i in range(3):
            try:
                response = requests.get(url, stream=True, timeout=5)
                if response.ok:
                    try:
                        img = Image.open(response.raw)
                        if isinstance(img, Image.Image):
                            return img
                        return self.get_fallback()

                    except (UnidentifiedImageError, OSError):
                        print(f"failed to open thumbnail: {url}")
                        return self.get_fallback()

                if response.status_code == 404:
                    return self.get_fallback()

            except (
                requests.exceptions.RequestException,
                requests.exceptions.ReadTimeout,
            ):
                print(f"{self.item_id}: retry thumbnail download {url}")
                sleep((i + 1) ** i)

        return self.get_fallback()

    def get_fallback(self):
        """get fallback thumbnail if not available"""
        print(f"{self.item_id}: failed to extract thumbnail, use fallback")
        if self.fallback:
            img_raw = Image.open(self.fallback)
            return img_raw

        app_root = EnvironmentSettings.APP_DIR
        default_map = {
            "video": os.path.join(
                app_root, "static/img/default-video-thumb.jpg"
            ),
            "playlist": os.path.join(
                app_root, "static/img/default-playlist-thumb.jpg"
            ),
            "icon": os.path.join(
                app_root, "static/img/default-channel-icon.jpg"
            ),
            "banner": os.path.join(
                app_root, "static/img/default-channel-banner.jpg"
            ),
            "tvart": os.path.join(
                app_root, "static/img/default-channel-art.jpg"
            ),
        }

        img_raw = Image.open(default_map[self.item_type])

        return img_raw


class ThumbManager(ThumbManagerBase):
    """handle thumbnails related functions"""

    def __init__(self, item_id, item_type="video", fallback=False):
        super().__init__(item_id, item_type, fallback=fallback)

    def download(self, url):
        """download thumbnail"""
        print(f"{self.item_id}: download {self.item_type} thumbnail")
        if self.item_type == "video":
            self.download_video_thumb(url)
        elif self.item_type == "channel":
            self.download_channel_art(url)
        elif self.item_type == "playlist":
            self.download_playlist_thumb(url)

    def delete(self):
        """delete thumbnail file"""
        print(f"{self.item_id}: delete {self.item_type} thumbnail")
        if self.item_type == "video":
            self.delete_video_thumb()
        elif self.item_type == "channel":
            self.delete_channel_thumb()
        elif self.item_type == "playlist":
            self.delete_playlist_thumb()

    def download_video_thumb(self, url, skip_existing=False):
        """pass url for video thumbnail"""
        folder_path = os.path.join(self.VIDEO_DIR, self.item_id[0].lower())
        thumb_path = self.vid_thumb_path(absolute=True)

        if skip_existing and os.path.exists(thumb_path):
            return

        os.makedirs(folder_path, exist_ok=True)
        img_raw = self.download_raw(url)
        width, height = img_raw.size

        if not width / height == 16 / 9:
            new_height = width / 16 * 9
            offset = (height - new_height) / 2
            img_raw = img_raw.crop((0, offset, width, height - offset))

        img_raw.convert("RGB").save(thumb_path)

    def vid_thumb_path(self, absolute=False, create_folder=False):
        """build expected path for video thumbnail from youtube_id"""
        folder_name = self.item_id[0].lower()
        folder_path = os.path.join("videos", folder_name)
        thumb_path = os.path.join(folder_path, f"{self.item_id}.jpg")
        if absolute:
            thumb_path = os.path.join(self.CACHE_DIR, thumb_path)

        if create_folder:
            folder_path = os.path.join(self.CACHE_DIR, folder_path)
            os.makedirs(folder_path, exist_ok=True)

        return thumb_path

    def download_channel_art(self, urls, skip_existing=False):
        """pass tuple of channel thumbnails"""
        channel_thumb, channel_banner, channel_tv = urls
        self._download_channel_thumb(channel_thumb, skip_existing)
        self._download_channel_banner(channel_banner, skip_existing)
        self._download_channel_tv(channel_tv, skip_existing)

    def _download_channel_thumb(self, channel_thumb, skip_existing):
        """download channel thumbnail"""

        thumb_path = os.path.join(
            self.CHANNEL_DIR, f"{self.item_id}_thumb.jpg"
        )
        self.item_type = "icon"

        if skip_existing and os.path.exists(thumb_path):
            return

        img_raw = self.download_raw(channel_thumb)
        img_raw.convert("RGB").save(thumb_path)

    def _download_channel_banner(self, channel_banner, skip_existing):
        """download channel banner"""

        banner_path = os.path.join(
            self.CHANNEL_DIR, self.item_id + "_banner.jpg"
        )
        self.item_type = "banner"
        if skip_existing and os.path.exists(banner_path):
            return

        img_raw = self.download_raw(channel_banner)
        img_raw.convert("RGB").save(banner_path)

    def _download_channel_tv(self, channel_tv, skip_existing):
        """download channel tv art"""
        art_path = os.path.join(self.CHANNEL_DIR, self.item_id + "_tvart.jpg")
        self.item_type = "tvart"
        if skip_existing and os.path.exists(art_path):
            return

        img_raw = self.download_raw(channel_tv)
        img_raw.convert("RGB").save(art_path)

    def download_playlist_thumb(self, url, skip_existing=False):
        """pass thumbnail url"""
        thumb_path = os.path.join(self.PLAYLIST_DIR, f"{self.item_id}.jpg")
        if skip_existing and os.path.exists(thumb_path):
            return

        img_raw = (
            self.download_raw(url)
            if not isinstance(url, str) or url.startswith("http")
            else Image.open(os.path.join(self.CACHE_DIR, url))
        )
        width, height = img_raw.size

        if not width / height == 16 / 9:
            new_height = width / 16 * 9
            offset = (height - new_height) / 2
            img_raw = img_raw.crop((0, offset, width, height - offset))
        img_raw = img_raw.resize((336, 189))
        img_raw.convert("RGB").save(thumb_path)

    def delete_video_thumb(self):
        """delete video thumbnail if exists"""
        thumb_path = self.vid_thumb_path()
        to_delete = os.path.join(self.CACHE_DIR, thumb_path)
        if os.path.exists(to_delete):
            os.remove(to_delete)

    def delete_channel_thumb(self):
        """delete all artwork of channel"""
        thumb = os.path.join(self.CHANNEL_DIR, f"{self.item_id}_thumb.jpg")
        banner = os.path.join(self.CHANNEL_DIR, f"{self.item_id}_banner.jpg")
        if os.path.exists(thumb):
            os.remove(thumb)
        if os.path.exists(banner):
            os.remove(banner)

    def delete_playlist_thumb(self):
        """delete playlist thumbnail"""
        thumb_path = os.path.join(self.PLAYLIST_DIR, f"{self.item_id}.jpg")
        if os.path.exists(thumb_path):
            os.remove(thumb_path)

    def get_vid_base64_blur(self):
        """return base64 encoded placeholder"""
        file_path = os.path.join(self.CACHE_DIR, self.vid_thumb_path())
        img_raw = Image.open(file_path)
        img_raw.thumbnail((img_raw.width // 20, img_raw.height // 20))
        img_blur = img_raw.filter(ImageFilter.BLUR)
        buffer = BytesIO()
        img_blur.save(buffer, format="JPEG")
        img_data = buffer.getvalue()
        img_base64 = base64.b64encode(img_data).decode()
        data_url = f"data:image/jpg;base64,{img_base64}"

        return data_url


class ValidatorCallback:
    """handle callback validate thumbnails page by page"""

    def __init__(self, source, index_name, counter=0):
        self.source = source
        self.index_name = index_name
        self.counter = counter

    def run(self):
        """run the task for page"""
        print(f"{self.index_name}: validate artwork")
        if self.index_name == "ta_video":
            self._validate_videos()
        elif self.index_name == "ta_channel":
            self._validate_channels()
        elif self.index_name == "ta_playlist":
            self._validate_playlists()

    def _validate_videos(self):
        """check if video thumbnails are correct"""
        for video in self.source:
            url = video["_source"]["vid_thumb_url"]
            handler = ThumbManager(video["_source"]["youtube_id"])
            handler.download_video_thumb(url, skip_existing=True)

    def _validate_channels(self):
        """check if all channel artwork is there"""
        for channel in self.source:
            urls = (
                channel["_source"]["channel_thumb_url"],
                channel["_source"]["channel_banner_url"],
                channel["_source"].get("channel_tvart_url", False),
            )
            handler = ThumbManager(channel["_source"]["channel_id"])
            handler.download_channel_art(urls, skip_existing=True)

    def _validate_playlists(self):
        """check if all playlist artwork is there"""
        for playlist in self.source:
            url = playlist["_source"]["playlist_thumbnail"]
            handler = ThumbManager(playlist["_source"]["playlist_id"])
            handler.download_playlist_thumb(url, skip_existing=True)


class ThumbValidator:
    """validate thumbnails"""

    INDEX = [
        {
            "data": {
                "query": {"term": {"active": {"value": True}}},
                "_source": ["vid_thumb_url", "youtube_id"],
            },
            "name": "ta_video",
        },
        {
            "data": {
                "query": {"term": {"channel_active": {"value": True}}},
                "_source": {
                    "excludes": ["channel_description", "channel_overwrites"]
                },
            },
            "name": "ta_channel",
        },
        {
            "data": {
                "query": {"term": {"playlist_active": {"value": True}}},
                "_source": ["playlist_id", "playlist_thumbnail"],
            },
            "name": "ta_playlist",
        },
    ]

    def __init__(self, task=False):
        self.task = task

    def validate(self):
        """validate all indexes"""
        for index in self.INDEX:
            total = self._get_total(index["name"])
            if not total:
                continue

            paginate = IndexPaginate(
                index_name=index["name"],
                data=index["data"],
                size=1000,
                callback=ValidatorCallback,
                task=self.task,
                total=total,
            )
            _ = paginate.get_results()

    def clean_up(self):
        """clean up all thumbs"""
        self._clean_up_vids()
        self._clean_up_channels()
        self._clean_up_playlists()

    def _clean_up_vids(self):
        """clean unneeded vid thumbs"""
        video_dir = os.path.join(EnvironmentSettings.CACHE_DIR, "videos")
        video_folders = os.listdir(video_dir)
        for video_folder in video_folders:
            folder_path = os.path.join(video_dir, video_folder)
            thumbs_is = {i.split(".")[0] for i in os.listdir(folder_path)}
            thumbs_should = self._get_vid_thumbs_should(video_folder)
            to_delete = thumbs_is - thumbs_should
            for thumb in to_delete:
                delete_path = os.path.join(folder_path, f"{thumb}.jpg")
                os.remove(delete_path)

            if to_delete:
                message = (
                    f"[thumbs][video][{video_folder}] "
                    + f"delete {len(to_delete)} unused thumbnails"
                )
                print(message)
                if self.task:
                    self.task.send_progress([message])

    @staticmethod
    def _get_vid_thumbs_should(video_folder: str) -> set[str]:
        """get indexed"""
        should_list = [
            {"prefix": {"youtube_id": {"value": video_folder.lower()}}},
            {"prefix": {"youtube_id": {"value": video_folder.upper()}}},
        ]
        data = {
            "query": {"bool": {"should": should_list}},
            "_source": ["youtube_id"],
        }
        result = IndexPaginate("ta_video,ta_download", data).get_results()
        thumbs_should = {i["youtube_id"] for i in result}

        return thumbs_should

    def _clean_up_channels(self):
        """clean unneeded channel thumbs"""
        channel_dir = os.path.join(EnvironmentSettings.CACHE_DIR, "channels")
        channel_art = os.listdir(channel_dir)
        thumbs_is = {"_".join(i.split("_")[:-1]) for i in channel_art}
        to_delete = is_missing(list(thumbs_is), "ta_channel", "channel_id")
        for channel_thumb in channel_art:
            if channel_thumb[:24] in to_delete:
                delete_path = os.path.join(channel_dir, channel_thumb)
                os.remove(delete_path)

        if to_delete:
            message = (
                "[thumbs][channel] "
                + f"delete {len(to_delete)} unused channel art"
            )
            print(message)
            if self.task:
                self.task.send_progress([message])

    def _clean_up_playlists(self):
        """clean up unneeded playlist thumbs"""
        playlist_dir = os.path.join(EnvironmentSettings.CACHE_DIR, "playlists")
        playlist_art = os.listdir(playlist_dir)
        thumbs_is = {i.split(".")[0] for i in playlist_art}
        to_delete = is_missing(list(thumbs_is), "ta_playlist", "playlist_id")
        for playlist_id in to_delete:
            delete_path = os.path.join(playlist_dir, f"{playlist_id}.jpg")
            os.remove(delete_path)

        if to_delete:
            message = (
                "[thumbs][playlist] "
                + f"delete {len(to_delete)} unused playlist art"
            )
            print(message)
            if self.task:
                self.task.send_progress([message])

    @staticmethod
    def _get_total(index_name):
        """get total documents in index"""
        path = f"{index_name}/_count"
        response, _ = ElasticWrap(path).get()

        return response.get("count")


class ThumbFilesystem:
    """sync thumbnail files to media files"""

    INDEX_NAME = "ta_video"

    def __init__(self, task=False):
        self.task = task

    def embed(self):
        """entry point"""
        data = {
            "query": {"match_all": {}},
            "_source": ["media_url", "youtube_id"],
        }
        paginate = IndexPaginate(
            index_name=self.INDEX_NAME,
            data=data,
            size=200,
            callback=EmbedCallback,
            task=self.task,
            total=self._get_total(),
        )
        _ = paginate.get_results()

    def _get_total(self):
        """get total documents in index"""
        path = f"{self.INDEX_NAME}/_count"
        response, _ = ElasticWrap(path).get()

        return response.get("count")


class EmbedCallback:
    """callback class to embed thumbnails"""

    CACHE_DIR = EnvironmentSettings.CACHE_DIR
    MEDIA_DIR = EnvironmentSettings.MEDIA_DIR
    FORMAT = MP4Cover.FORMAT_JPEG

    def __init__(self, source, index_name, counter=0):
        self.source = source
        self.index_name = index_name
        self.counter = counter

    def run(self):
        """run embed"""
        for video in self.source:
            video_id = video["_source"]["youtube_id"]
            media_url = os.path.join(
                self.MEDIA_DIR, video["_source"]["media_url"]
            )
            thumb_path = os.path.join(
                self.CACHE_DIR, ThumbManager(video_id).vid_thumb_path()
            )
            if os.path.exists(thumb_path):
                self.embed(media_url, thumb_path)

    def embed(self, media_url, thumb_path):
        """embed thumb in single media file"""
        video = MP4(media_url)
        with open(thumb_path, "rb") as f:
            video["covr"] = [MP4Cover(f.read(), imageformat=self.FORMAT)]

        video.save()
