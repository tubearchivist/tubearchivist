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
from datetime import datetime
from math import ceil
from time import sleep

import requests
from home.src.config import AppConfig
from home.src.download import ChannelSubscription, PendingList, VideoDownloader
from home.src.helper import (
    clean_string,
    get_message,
    get_total_hits,
    ignore_filelist,
    set_message,
)
from home.src.index import YoutubeChannel, YoutubeVideo, index_new_video


class Reindex:
    """check for outdated documents and refresh data from youtube"""

    def __init__(self):
        # config
        config = AppConfig().config
        self.sleep_interval = config["downloads"]["sleep_interval"]
        self.es_url = config["application"]["es_url"]
        self.refresh_interval = 90
        # scan
        self.video_daily, self.channel_daily = self.get_daily()
        self.all_youtube_ids = False
        self.all_channel_ids = False

    def get_daily(self):
        """get daily refresh values"""
        total_videos = get_total_hits("ta_video", self.es_url, "active")
        video_daily = ceil(total_videos / self.refresh_interval * 1.2)
        total_channels = get_total_hits(
            "ta_channel", self.es_url, "channel_active"
        )
        channel_daily = ceil(total_channels / self.refresh_interval * 1.2)
        return (video_daily, channel_daily)

    def get_outdated_vids(self):
        """get daily videos to refresh"""
        headers = {"Content-type": "application/json"}
        now = int(datetime.now().strftime("%s"))
        now_3m = now - 3 * 30 * 24 * 60 * 60
        size = self.video_daily
        data = {
            "size": size,
            "query": {
                "bool": {
                    "must": [
                        {"match": {"active": True}},
                        {"range": {"vid_last_refresh": {"lte": now_3m}}},
                    ]
                }
            },
            "sort": [{"vid_last_refresh": {"order": "asc"}}],
            "_source": False,
        }
        query_str = json.dumps(data)
        url = self.es_url + "/ta_video/_search"
        response = requests.get(url, data=query_str, headers=headers)
        if not response.ok:
            print(response.text)
        response_dict = json.loads(response.text)
        all_youtube_ids = [i["_id"] for i in response_dict["hits"]["hits"]]
        return all_youtube_ids

    def get_outdated_channels(self):
        """get daily channels to refresh"""
        headers = {"Content-type": "application/json"}
        now = int(datetime.now().strftime("%s"))
        now_3m = now - 3 * 30 * 24 * 60 * 60
        size = self.channel_daily
        data = {
            "size": size,
            "query": {
                "bool": {
                    "must": [
                        {"match": {"channel_active": True}},
                        {"range": {"channel_last_refresh": {"lte": now_3m}}},
                    ]
                }
            },
            "sort": [{"channel_last_refresh": {"order": "asc"}}],
            "_source": False,
        }
        query_str = json.dumps(data)
        url = self.es_url + "/ta_channel/_search"
        response = requests.get(url, data=query_str, headers=headers)
        if not response.ok:
            print(response.text)
        response_dict = json.loads(response.text)
        all_channel_ids = [i["_id"] for i in response_dict["hits"]["hits"]]
        return all_channel_ids

    def check_outdated(self):
        """add missing vids and channels"""
        self.all_youtube_ids = self.get_outdated_vids()
        self.all_channel_ids = self.get_outdated_channels()

    def rescrape_all_channels(self):
        """sync new data from channel to all matching videos"""
        sleep_interval = self.sleep_interval
        channel_sub_handler = ChannelSubscription()
        all_channels = channel_sub_handler.get_channels(subscribed_only=False)
        all_channel_ids = [i["channel_id"] for i in all_channels]

        counter = 1
        for channel_id in all_channel_ids:
            message = f"Progress: {counter}/{len(all_channels)}"
            mess_dict = {
                "status": "scraping",
                "level": "info",
                "title": "Scraping all youtube channels",
                "message": message,
            }
            set_message("progress:download", mess_dict)
            channel_index = YoutubeChannel(channel_id)
            subscribed = channel_index.channel_dict["channel_subscribed"]
            channel_index.channel_dict = channel_index.build_channel_dict(
                scrape=True
            )
            channel_index.channel_dict["channel_subscribed"] = subscribed
            channel_index.upload_to_es()
            channel_index.sync_to_videos()
            counter = counter + 1
            if sleep_interval:
                sleep(sleep_interval)

    @staticmethod
    def reindex_single_video(youtube_id):
        """refresh data for single video"""
        vid_handler = YoutubeVideo(youtube_id)
        if not vid_handler.vid_dict:
            # stop if deactivated
            vid_handler.deactivate()
            return

        es_vid_dict = vid_handler.get_es_data()
        player = es_vid_dict["_source"]["player"]
        date_downloaded = es_vid_dict["_source"]["date_downloaded"]
        channel_dict = es_vid_dict["_source"]["channel"]
        channel_name = channel_dict["channel_name"]
        vid_handler.build_file_path(channel_name)
        # add to vid_dict
        vid_handler.vid_dict["player"] = player
        vid_handler.vid_dict["date_downloaded"] = date_downloaded
        vid_handler.vid_dict["channel"] = channel_dict
        # update
        vid_handler.upload_to_es()
        vid_handler.delete_cache()

    @staticmethod
    def reindex_single_channel(channel_id):
        """refresh channel data and sync to videos"""
        channel_handler = YoutubeChannel(channel_id)
        subscribed = channel_handler.channel_dict["channel_subscribed"]
        channel_handler.channel_dict = channel_handler.build_channel_dict(
            scrape=True
        )
        channel_handler.channel_dict["channel_subscribed"] = subscribed
        channel_handler.upload_to_es()
        channel_handler.sync_to_videos()
        channel_handler.clear_cache()

    def reindex(self):
        """reindex what's needed"""
        # videos
        print(f"reindexing {len(self.all_youtube_ids)} videos")
        for youtube_id in self.all_youtube_ids:
            self.reindex_single_video(youtube_id)
            if self.sleep_interval:
                sleep(self.sleep_interval)
        # channels
        print(f"reindexing {len(self.all_channel_ids)} channels")
        for channel_id in self.all_channel_ids:
            self.reindex_single_channel(channel_id)
            if self.sleep_interval:
                sleep(self.sleep_interval)


class FilesystemScanner:
    """handle scanning and fixing from filesystem"""

    CONFIG = AppConfig().config
    ES_URL = CONFIG["application"]["es_url"]
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
            videos = os.listdir(channel_path)
            all_videos = ignore_filelist(videos)
            for video in all_videos:
                youtube_id = video[9:20]
                all_downloaded.append((channel_name, video, youtube_id))

        return all_downloaded

    @staticmethod
    def get_all_indexed():
        """get a list of all indexed videos"""
        index_handler = PendingList()
        all_indexed_raw = index_handler.get_all_indexed()
        all_indexed = []
        for video in all_indexed_raw:
            youtube_id = video["_id"]
            media_url = video["_source"]["media_url"]
            published = video["_source"]["published"]
            title = video["_source"]["title"]
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
            old_path = os.path.join(self.VIDEOS, channel, filename)
            new_path = os.path.join(self.VIDEOS, channel, expected_filename)
            os.rename(old_path, new_path)

    def send_mismatch_bulk(self):
        """build bulk update"""
        bulk_list = []
        for video_mismatch in self.mismatch:
            youtube_id, media_url = video_mismatch
            action = {"update": {"_id": youtube_id, "_index": "ta_video"}}
            source = {"doc": {"media_url": media_url}}
            bulk_list.append(json.dumps(action))
            bulk_list.append(json.dumps(source))
        # add last newline
        bulk_list.append("\n")
        query_str = "\n".join(bulk_list)
        # make the call
        headers = {"Content-type": "application/x-ndjson"}
        url = self.ES_URL + "/_bulk"
        request = requests.post(url, data=query_str, headers=headers)
        if not request.ok:
            print(request.text)

    def delete_from_index(self):
        """find indexed but deleted mediafile"""
        for indexed in self.to_delete:
            youtube_id, _ = indexed
            url = self.ES_URL + "/ta_video/_doc/" + youtube_id
            request = requests.delete(url)
            if not request.ok:
                print(request.text)


class ManualImport:
    """import and indexing existing video files"""

    CONFIG = AppConfig().config
    CACHE_DIR = CONFIG["application"]["cache_dir"]
    IMPORT_DIR = os.path.join(CACHE_DIR, "import")

    def __init__(self):
        self.identified = self.import_folder_parser()

    def import_folder_parser(self):
        """detect files in import folder"""
        import_files = os.listdir(self.IMPORT_DIR)
        to_import = ignore_filelist(import_files)
        to_import.sort()
        video_files = [i for i in to_import if not i.endswith(".json")]

        identified = []

        for file_path in video_files:

            file_dict = {"video_file": file_path}
            file_name, _ = os.path.splitext(file_path)

            matching_json = [
                i
                for i in to_import
                if i.startswith(file_name) and i.endswith(".json")
            ]
            if matching_json:
                json_file = matching_json[0]
                youtube_id = self.extract_id_from_json(json_file)
                file_dict.update({"json_file": json_file})
            else:
                youtube_id = self.extract_id_from_filename(file_name)
                file_dict.update({"json_file": False})

            file_dict.update({"youtube_id": youtube_id})
            identified.append(file_dict)

        return identified

    @staticmethod
    def extract_id_from_filename(file_name):
        """
        look at the file name for the youtube id
        expects filename ending in [<youtube_id>].<ext>
        """
        id_search = re.search(r"\[([a-zA-Z0-9_-]{11})\]$", file_name)
        if id_search:
            youtube_id = id_search.group(1)
            return youtube_id

        print("failed to extract youtube id for: " + file_name)
        raise Exception

    def extract_id_from_json(self, json_file):
        """open json file and extract id"""
        json_path = os.path.join(self.CACHE_DIR, "import", json_file)
        with open(json_path, "r", encoding="utf-8") as f:
            json_content = f.read()

        youtube_id = json.loads(json_content)["id"]

        return youtube_id

    def process_import(self):
        """go through identified media files"""

        for media_file in self.identified:
            json_file = media_file["json_file"]
            video_file = media_file["video_file"]
            youtube_id = media_file["youtube_id"]

            video_path = os.path.join(self.CACHE_DIR, "import", video_file)

            self.move_to_cache(video_path, youtube_id)

            # identify and archive
            vid_dict = index_new_video(youtube_id)
            VideoDownloader([youtube_id]).move_to_archive(vid_dict)

            # cleanup
            if os.path.exists(video_path):
                os.remove(video_path)
            if json_file:
                json_path = os.path.join(self.CACHE_DIR, "import", json_file)
                os.remove(json_path)

    def move_to_cache(self, video_path, youtube_id):
        """move identified video file to cache, convert to mp4"""
        file_name = os.path.split(video_path)[-1]
        video_file, ext = os.path.splitext(file_name)

        # make sure youtube_id is in filename
        if youtube_id not in video_file:
            video_file = f"{video_file}_{youtube_id}"

        # move, convert if needed
        if ext == ".mp4":
            new_file = video_file + ext
            dest_path = os.path.join(self.CACHE_DIR, "download", new_file)
            shutil.move(video_path, dest_path)
        else:
            print(f"processing with ffmpeg: {video_file}")
            new_file = video_file + ".mp4"
            dest_path = os.path.join(self.CACHE_DIR, "download", new_file)
            subprocess.run(
                [
                    "ffmpeg",
                    "-i",
                    video_path,
                    dest_path,
                    "-loglevel",
                    "warning",
                    "-stats",
                ],
                check=True,
            )


def scan_filesystem():
    """grouped function to delete and update index"""
    filesystem_handler = FilesystemScanner()
    filesystem_handler.list_comarison()
    if filesystem_handler.to_rename:
        filesystem_handler.rename_files()
    if filesystem_handler.mismatch:
        filesystem_handler.send_mismatch_bulk()
    if filesystem_handler.to_delete:
        filesystem_handler.delete_from_index()
    if filesystem_handler.to_index:
        for missing_vid in filesystem_handler.to_index:
            youtube_id = missing_vid[2]
            index_new_video(youtube_id, missing_vid=missing_vid)


def reindex_old_documents():
    """daily refresh of old documents"""
    # check needed last run
    now = int(datetime.now().strftime("%s"))
    last_reindex = get_message("last_reindex")
    if isinstance(last_reindex, int) and now - last_reindex < 60 * 60 * 24:
        return
    # continue if needed
    reindex_handler = Reindex()
    reindex_handler.check_outdated()
    reindex_handler.reindex()
    # set timestamp
    set_message("last_reindex", now, expire=False)
