"""
Functionality:
- reindexing old documents
- syncing updated values between indexes
- scan the filesystem to delete or index
"""

import json
import os

from home.src.download.queue import PendingList
from home.src.es.connect import ElasticWrap
from home.src.index.comments import CommentList
from home.src.index.video import index_new_video
from home.src.ta.config import AppConfig
from home.src.ta.helper import clean_string, ignore_filelist
from PIL import ImageFile

ImageFile.LOAD_TRUNCATED_IMAGES = True


class ScannerBase:
    """scan the filesystem base class"""

    CONFIG = AppConfig().config
    VIDEOS = CONFIG["application"]["videos"]

    def __init__(self):
        self.to_index = False
        self.to_delete = False
        self.mismatch = False
        self.to_rename = False

    def scan(self):
        """entry point, scan and compare"""
        all_downloaded = self._get_all_downloaded()
        all_indexed = self._get_all_indexed()
        self.list_comarison(all_downloaded, all_indexed)

    def _get_all_downloaded(self):
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
    def _get_all_indexed():
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

    def list_comarison(self, all_downloaded, all_indexed):
        """compare the lists to figure out what to do"""
        self._find_unindexed(all_downloaded, all_indexed)
        self._find_missing(all_downloaded, all_indexed)
        self._find_bad_media_url(all_downloaded, all_indexed)

    def _find_unindexed(self, all_downloaded, all_indexed):
        """find video files without a matching document indexed"""
        all_indexed_ids = [i[0] for i in all_indexed]
        self.to_index = []
        for downloaded in all_downloaded:
            if downloaded[2] not in all_indexed_ids:
                self.to_index.append(downloaded)

    def _find_missing(self, all_downloaded, all_indexed):
        """find indexed videos without matching media file"""
        all_downloaded_ids = [i[2] for i in all_downloaded]
        self.to_delete = []
        for video in all_indexed:
            youtube_id = video[0]
            if youtube_id not in all_downloaded_ids:
                self.to_delete.append(video)

    def _find_bad_media_url(self, all_downloaded, all_indexed):
        """rename media files not matching the indexed title"""
        self.mismatch = []
        self.to_rename = []

        for downloaded in all_downloaded:
            channel, filename, downloaded_id = downloaded
            # find in indexed
            for indexed in all_indexed:
                indexed_id, media_url, published, title = indexed
                if indexed_id == downloaded_id:
                    # found it
                    pub = published.replace("-", "")
                    expected = f"{pub}_{indexed_id}_{clean_string(title)}.mp4"
                    new_url = os.path.join(channel, expected)
                    if expected != filename:
                        # file to rename
                        self.to_rename.append((channel, filename, expected))
                    if media_url != new_url:
                        # media_url to update in es
                        self.mismatch.append((indexed_id, new_url))

                    break


class Filesystem(ScannerBase):
    """handle scanning and fixing from filesystem"""

    def __init__(self, task=False):
        super().__init__()
        self.task = task

    def process(self):
        """entry point"""
        self.task.send_progress(["Scanning your archive and index."])
        self.scan()
        self.rename_files()
        self.send_mismatch_bulk()
        self.delete_from_index()
        self.add_missing()

    def rename_files(self):
        """rename media files as identified by find_bad_media_url"""
        if not self.to_rename:
            return

        total = len(self.to_rename)
        self.task.send_progress([f"Rename {total} media files."])
        for bad_filename in self.to_rename:
            channel, filename, expected_filename = bad_filename
            print(f"renaming [{filename}] to [{expected_filename}]")
            old_path = os.path.join(self.VIDEOS, channel, filename)
            new_path = os.path.join(self.VIDEOS, channel, expected_filename)
            os.rename(old_path, new_path)

    def send_mismatch_bulk(self):
        """build bulk update"""
        if not self.mismatch:
            return

        total = len(self.mismatch)
        self.task.send_progress([f"Fix media urls for {total} files"])
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
        if not self.to_delete:
            return

        total = len(self.to_delete)
        self.task.send_progress([f"Clean up {total} items from index."])
        for indexed in self.to_delete:
            youtube_id = indexed[0]
            print(f"deleting {youtube_id} from index")
            path = f"ta_video/_doc/{youtube_id}"
            _, _ = ElasticWrap(path).delete()

    def add_missing(self):
        """add missing videos to index"""
        video_ids = [i[2] for i in self.to_index]
        if not video_ids:
            return

        total = len(video_ids)
        for idx, youtube_id in enumerate(video_ids):
            if self.task:
                self.task.send_progress(
                    message_lines=[
                        f"Index missing video {youtube_id}, {idx}/{total}"
                    ],
                    progress=(idx + 1) / total,
                )
            index_new_video(youtube_id)

        CommentList(video_ids, task=self.task).index()
