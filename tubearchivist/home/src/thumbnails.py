"""
functionality:
- handle download and caching for thumbnails
"""

import os

import home.src.download as download
import requests
from home.src.config import AppConfig
from home.src.helper import RedisArchivist, ignore_filelist
from PIL import Image


class ThumbManager:
    """handle thumbnails related functions"""

    CONFIG = AppConfig().config
    CACHE_DIR = CONFIG["application"]["cache_dir"]
    VIDEO_DIR = os.path.join(CACHE_DIR, "videos")
    CHANNEL_DIR = os.path.join(CACHE_DIR, "channels")

    def get_all_thumbs(self):
        """get all video artwork already downloaded"""
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

    def get_needed_thumbs(self, missing_only=False):
        """get a list of all missing thumbnails"""
        all_thumbs = self.get_all_thumbs()
        all_indexed = download.PendingList().get_all_indexed()
        all_in_queue, all_ignored = download.PendingList().get_all_pending()

        needed_thumbs = []
        for video in all_indexed:
            youtube_id = video["_source"]["youtube_id"]
            thumb_url = video["_source"]["vid_thumb_url"]
            if missing_only:
                if youtube_id + ".jpg" not in all_thumbs:
                    needed_thumbs.append((youtube_id, thumb_url))
            else:
                needed_thumbs.append((youtube_id, thumb_url))

        for video in all_in_queue + all_ignored:
            youtube_id = video["youtube_id"]
            thumb_url = video["vid_thumb_url"]
            if missing_only:
                if youtube_id + ".jpg" not in all_thumbs:
                    needed_thumbs.append((youtube_id, thumb_url))
            else:
                needed_thumbs.append((youtube_id, thumb_url))

        return needed_thumbs

    def get_missing_channels(self):
        """get all channel artwork"""
        all_channel_art = os.listdir(self.CHANNEL_DIR)
        cached_channel_ids = {i[0:24] for i in all_channel_art}
        channels = download.ChannelSubscription().get_channels(
            subscribed_only=False
        )

        missing_channels = []
        for channel in channels:
            channel_id = channel["channel_id"]
            if channel_id not in cached_channel_ids:
                channel_banner = channel["channel_banner_url"]
                channel_thumb = channel["channel_thumb_url"]
                missing_channels.append(
                    (channel_id, channel_thumb, channel_banner)
                )

        return missing_channels

    def get_raw_img(self, img_url, thumb_type):
        """get raw image from youtube and handle 404"""
        app_root = self.CONFIG["application"]["app_root"]
        default_map = {
            "video": os.path.join(
                app_root, "static/img/default-video-thumb.jpg"
            ),
            "icon": os.path.join(
                app_root, "static/img/default-channel-icon.jpg"
            ),
            "banner": os.path.join(
                app_root, "static/img/default-channel-banner.jpg"
            ),
        }
        if img_url:
            response = requests.get(img_url, stream=True)
        else:
            response = False
        if not response or response.status_code == 404:
            # use default
            img_raw = Image.open(default_map[thumb_type])
        else:
            # use response
            img_obj = response.raw
            img_raw = Image.open(img_obj)

        return img_raw

    def download_vid(self, missing_thumbs):
        """download all missing thumbnails from list"""
        print(f"downloading {len(missing_thumbs)} thumbnails")
        # videos
        for youtube_id, thumb_url in missing_thumbs:
            folder_name = youtube_id[0].lower()
            folder_path = os.path.join(self.VIDEO_DIR, folder_name)
            thumb_path_part = self.vid_thumb_path(youtube_id)
            thumb_path = os.path.join(self.CACHE_DIR, thumb_path_part)

            os.makedirs(folder_path, exist_ok=True)
            img_raw = self.get_raw_img(thumb_url, "video")

            width, height = img_raw.size
            if not width / height == 16 / 9:
                new_height = width / 16 * 9
                offset = (height - new_height) / 2
                img_raw = img_raw.crop((0, offset, width, height - offset))

            img_raw.convert("RGB").save(thumb_path)

            mess_dict = {
                "status": "pending",
                "level": "info",
                "title": "Adding to download queue.",
                "message": "Downloading Thumbnails...",
            }
            RedisArchivist().set_message("progress:download", mess_dict)

    def download_chan(self, missing_channels):
        """download needed artwork for channels"""
        print(f"downloading {len(missing_channels)} channel artwork")
        for channel in missing_channels:
            channel_id, channel_thumb, channel_banner = channel

            thumb_path = os.path.join(
                self.CHANNEL_DIR, channel_id + "_thumb.jpg"
            )
            img_raw = self.get_raw_img(channel_thumb, "icon")
            img_raw.convert("RGB").save(thumb_path)

            banner_path = os.path.join(
                self.CHANNEL_DIR, channel_id + "_banner.jpg"
            )
            img_raw = self.get_raw_img(channel_banner, "banner")
            img_raw.convert("RGB").save(banner_path)

            mess_dict = {
                "status": "pending",
                "level": "info",
                "title": "Adding to download queue.",
                "message": "Downloading Channel Art...",
            }
            RedisArchivist().set_message("progress:download", mess_dict)

    @staticmethod
    def vid_thumb_path(youtube_id):
        """build expected path for video thumbnail from youtube_id"""
        folder_name = youtube_id[0].lower()
        folder_path = os.path.join("videos", folder_name)
        thumb_path = os.path.join(folder_path, youtube_id + ".jpg")
        return thumb_path

    def delete_vid_thumb(self, youtube_id):
        """delete video thumbnail if exists"""
        thumb_path = self.vid_thumb_path(youtube_id)
        to_delete = os.path.join(self.CACHE_DIR, thumb_path)
        if os.path.exists(to_delete):
            os.remove(to_delete)

    def delete_chan_thumb(self, channel_id):
        """delete all artwork of channel"""
        thumb = os.path.join(self.CHANNEL_DIR, channel_id + "_thumb.jpg")
        banner = os.path.join(self.CHANNEL_DIR, channel_id + "_banner.jpg")
        if os.path.exists(thumb):
            os.remove(thumb)
        if os.path.exists(banner):
            os.remove(banner)

    def cleanup_downloaded(self):
        """find downloaded thumbnails without video indexed"""
        all_thumbs = self.get_all_thumbs()
        all_indexed = self.get_needed_thumbs()
        all_needed_thumbs = [i[0] + ".jpg" for i in all_indexed]
        for thumb in all_thumbs:
            if thumb not in all_needed_thumbs:
                # cleanup
                youtube_id = thumb.rstrip(".jpg")
                self.delete_vid_thumb(youtube_id)


def validate_thumbnails():
    """check if all thumbnails are there and organized correctly"""
    handler = ThumbManager()
    thumbs_to_download = handler.get_needed_thumbs(missing_only=True)
    handler.download_vid(thumbs_to_download)
    missing_channels = handler.get_missing_channels()
    handler.download_chan(missing_channels)
    handler.cleanup_downloaded()
