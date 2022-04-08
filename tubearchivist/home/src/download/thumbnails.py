"""
functionality:
- handle download and caching for thumbnails
- check for missing thumbnails
"""

import base64
import os
from collections import Counter
from io import BytesIO
from time import sleep

import requests
from home.src.download import queue  # partial import
from home.src.download import subscriptions  # partial import
from home.src.ta.config import AppConfig
from home.src.ta.helper import ignore_filelist
from home.src.ta.ta_redis import RedisArchivist
from mutagen.mp4 import MP4, MP4Cover
from PIL import Image, ImageFilter


class ThumbManager:
    """handle thumbnails related functions"""

    CONFIG = AppConfig().config
    MEDIA_DIR = CONFIG["application"]["videos"]
    CACHE_DIR = CONFIG["application"]["cache_dir"]
    VIDEO_DIR = os.path.join(CACHE_DIR, "videos")
    CHANNEL_DIR = os.path.join(CACHE_DIR, "channels")
    PLAYLIST_DIR = os.path.join(CACHE_DIR, "playlists")

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

        pending = queue.PendingList()
        pending.get_download()
        pending.get_indexed()

        needed_thumbs = []
        for video in pending.all_videos:
            youtube_id = video["youtube_id"]
            thumb_url = video["vid_thumb_url"]
            if missing_only:
                if youtube_id + ".jpg" not in all_thumbs:
                    needed_thumbs.append((youtube_id, thumb_url))
            else:
                needed_thumbs.append((youtube_id, thumb_url))

        for video in pending.all_pending + pending.all_ignored:
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
        files = [i[0:24] for i in all_channel_art]
        cached_channel_ids = [k for (k, v) in Counter(files).items() if v > 1]
        channel_sub = subscriptions.ChannelSubscription()
        channels = channel_sub.get_channels(subscribed_only=False)

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

    def get_missing_playlists(self):
        """get all missing playlist artwork"""
        all_downloaded = ignore_filelist(os.listdir(self.PLAYLIST_DIR))
        all_ids_downloaded = [i.replace(".jpg", "") for i in all_downloaded]
        playlist_sub = subscriptions.PlaylistSubscription()
        playlists = playlist_sub.get_playlists(subscribed_only=False)

        missing_playlists = []
        for playlist in playlists:
            playlist_id = playlist["playlist_id"]
            if playlist_id not in all_ids_downloaded:
                playlist_thumb = playlist["playlist_thumbnail"]
                missing_playlists.append((playlist_id, playlist_thumb))

        return missing_playlists

    def get_raw_img(self, img_url, thumb_type):
        """get raw image from youtube and handle 404"""
        try:
            app_root = self.CONFIG["application"]["app_root"]
        except KeyError:
            # lazy keyerror fix to not have to deal with a strange startup
            # racing contition between the threads in HomeConfig.ready()
            app_root = "/app"
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
            try:
                response = requests.get(img_url, stream=True)
            except ConnectionError:
                sleep(5)
                response = requests.get(img_url, stream=True)
            if not response.ok and not response.status_code == 404:
                print("retry thumbnail download for " + img_url)
                sleep(5)
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

    def download_vid(self, missing_thumbs, notify=True):
        """download all missing thumbnails from list"""
        print(f"downloading {len(missing_thumbs)} thumbnails")
        for idx, (youtube_id, thumb_url) in enumerate(missing_thumbs):
            folder_path = os.path.join(self.VIDEO_DIR, youtube_id[0].lower())
            thumb_path = os.path.join(
                self.CACHE_DIR, self.vid_thumb_path(youtube_id)
            )

            os.makedirs(folder_path, exist_ok=True)
            img_raw = self.get_raw_img(thumb_url, "video")

            width, height = img_raw.size
            if not width / height == 16 / 9:
                new_height = width / 16 * 9
                offset = (height - new_height) / 2
                img_raw = img_raw.crop((0, offset, width, height - offset))
            img_raw.convert("RGB").save(thumb_path)

            progress = f"{idx + 1}/{len(missing_thumbs)}"
            if notify:
                mess_dict = {
                    "status": "message:add",
                    "level": "info",
                    "title": "Processing Videos",
                    "message": "Downloading Thumbnails, Progress: " + progress,
                }
                if idx + 1 == len(missing_thumbs):
                    RedisArchivist().set_message(
                        "message:add", mess_dict, expire=4
                    )
                else:
                    RedisArchivist().set_message("message:add", mess_dict)

            if idx + 1 % 25 == 0:
                print("thumbnail progress: " + progress)

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
                "status": "message:download",
                "level": "info",
                "title": "Processing Channels",
                "message": "Downloading Channel Art.",
            }
            RedisArchivist().set_message("message:download", mess_dict)

    def download_playlist(self, missing_playlists):
        """download needed artwork for playlists"""
        print(f"downloading {len(missing_playlists)} playlist artwork")
        for playlist in missing_playlists:
            playlist_id, playlist_thumb_url = playlist
            thumb_path = os.path.join(self.PLAYLIST_DIR, playlist_id + ".jpg")
            img_raw = self.get_raw_img(playlist_thumb_url, "video")
            img_raw.convert("RGB").save(thumb_path)

            mess_dict = {
                "status": "message:download",
                "level": "info",
                "title": "Processing Playlists",
                "message": "Downloading Playlist Art.",
            }
            RedisArchivist().set_message("message:download", mess_dict)

    def get_base64_blur(self, youtube_id):
        """return base64 encoded placeholder"""
        img_path = self.vid_thumb_path(youtube_id)
        file_path = os.path.join(self.CACHE_DIR, img_path)
        img_raw = Image.open(file_path)
        img_raw.thumbnail((img_raw.width // 20, img_raw.height // 20))
        img_blur = img_raw.filter(ImageFilter.BLUR)
        buffer = BytesIO()
        img_blur.save(buffer, format="JPEG")
        img_data = buffer.getvalue()
        img_base64 = base64.b64encode(img_data).decode()
        data_url = f"data:image/jpg;base64,{img_base64}"

        return data_url

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

    def get_thumb_list(self):
        """get list of mediafiles and matching thumbnails"""
        pending = queue.PendingList()
        pending.get_indexed()

        video_list = []
        for video in pending.all_videos:
            youtube_id = video["youtube_id"]
            media_url = os.path.join(self.MEDIA_DIR, video["media_url"])
            thumb_path = os.path.join(
                self.CACHE_DIR, self.vid_thumb_path(youtube_id)
            )
            video_list.append(
                {
                    "media_url": media_url,
                    "thumb_path": thumb_path,
                }
            )

        return video_list

    @staticmethod
    def write_all_thumbs(video_list):
        """rewrite the thumbnail into media file"""

        counter = 1
        for video in video_list:
            # loop through all videos
            media_url = video["media_url"]
            thumb_path = video["thumb_path"]

            mutagen_vid = MP4(media_url)
            with open(thumb_path, "rb") as f:
                mutagen_vid["covr"] = [
                    MP4Cover(f.read(), imageformat=MP4Cover.FORMAT_JPEG)
                ]
            mutagen_vid.save()
            if counter % 50 == 0:
                print(f"thumbnail write progress {counter}/{len(video_list)}")
            counter = counter + 1


def validate_thumbnails():
    """check if all thumbnails are there and organized correctly"""
    handler = ThumbManager()
    thumbs_to_download = handler.get_needed_thumbs(missing_only=True)
    handler.download_vid(thumbs_to_download)
    missing_channels = handler.get_missing_channels()
    handler.download_chan(missing_channels)
    missing_playlists = handler.get_missing_playlists()
    handler.download_playlist(missing_playlists)
    handler.cleanup_downloaded()
