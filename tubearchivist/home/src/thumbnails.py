"""
functionality:
- handle download and caching for thumbnails
"""

import os

import requests
from home.src.config import AppConfig
from home.src.download import PendingList
from home.src.helper import RedisArchivist, ignore_filelist
from PIL import Image


class ThumbManager:
    """handle thumbnails related functions"""

    CONFIG = AppConfig().config
    CACHE_DIR = CONFIG["application"]["cache_dir"]
    VIDEO_DIR = os.path.join(CACHE_DIR, "videos")

    def get_all_thumbs(self):
        """raise exception if cache not clean"""
        all_thumb_folders = ignore_filelist(os.listdir(self.VIDEO_DIR))
        all_thumbs = []
        for folder in all_thumb_folders:
            folder_path = os.path.join(self.VIDEO_DIR, folder)
            if os.path.isfile(folder_path):
                self.update_path(folder)
                all_thumbs.append(folder_path)
                continue
                # raise exemption here in a future version
                # raise FileExistsError("video cache dir has files inside")

            all_folder_thumbs = ignore_filelist(os.listdir(folder_path))
            all_thumbs.extend(all_folder_thumbs)

        return all_thumbs

    def update_path(self, file_name):
        """reorganize thumbnails into folders as update path from v0.0.5"""
        folder_name = file_name[0].lower()
        folder_path = os.path.join(self.VIDEO_DIR, folder_name)
        old_file = os.path.join(self.VIDEO_DIR, file_name)
        new_file = os.path.join(folder_path, file_name)
        os.makedirs(folder_path, exist_ok=True)
        os.rename(old_file, new_file)

    def get_missing_thumbs(self):
        """get a list of all missing thumbnails"""
        all_thumbs = self.get_all_thumbs()
        all_indexed = PendingList().get_all_indexed()
        all_in_queue, all_ignored = PendingList().get_all_pending()

        missing_thumbs = []
        for video in all_indexed:
            youtube_id = video["_source"]["youtube_id"]
            if youtube_id + ".jpg" not in all_thumbs:
                thumb_url = video["_source"]["vid_thumb_url"]
                missing_thumbs.append((youtube_id, thumb_url))

        for video in all_in_queue + all_ignored:
            youtube_id = video["youtube_id"]
            if youtube_id + ".jpg" not in all_thumbs:
                thumb_url = video["vid_thumb_url"]
                missing_thumbs.append((youtube_id, thumb_url))

        return missing_thumbs

    def download_missing(self, missing_thumbs):
        """download all missing thumbnails from list"""
        print(f"downloading {len(missing_thumbs)} thumbnails")
        vid_cache = os.path.join(self.CACHE_DIR, "videos")
        # videos
        for youtube_id, thumb_url in missing_thumbs:
            folder_name = youtube_id[0].lower()
            folder_path = os.path.join(vid_cache, folder_name)
            thumb_path_part = self.vid_thumb_path(youtube_id)
            thumb_path = os.path.join(self.CACHE_DIR, thumb_path_part)

            os.makedirs(folder_path, exist_ok=True)
            img_raw = requests.get(thumb_url, stream=True).raw
            img = Image.open(img_raw)

            width, height = img.size
            if not width / height == 16 / 9:
                new_height = width / 16 * 9
                offset = (height - new_height) / 2
                img = img.crop((0, offset, width, height - offset))

            img.convert("RGB").save(thumb_path)

            mess_dict = {
                "status": "pending",
                "level": "info",
                "title": "Adding to download queue.",
                "message": "Downloading Thumbnails...",
            }
            RedisArchivist().set_message("progress:download", mess_dict)

    @staticmethod
    def vid_thumb_path(youtube_id):
        """build expected path for video thumbnail from youtube_id"""
        folder_name = youtube_id[0].lower()
        folder_path = os.path.join("videos", folder_name)
        thumb_path = os.path.join(folder_path, youtube_id + ".jpg")
        return thumb_path


def validate_thumbnails():
    """check if all thumbnails are there and organized correctly"""
    handler = ThumbManager()
    thumbs_to_download = handler.get_missing_thumbs()
    handler.download_missing(thumbs_to_download)
