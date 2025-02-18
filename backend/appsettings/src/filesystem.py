"""
Functionality:
- scan the filesystem to delete or index
"""

import os

from common.src.env_settings import EnvironmentSettings
from common.src.es_connect import IndexPaginate
from common.src.helper import ignore_filelist
from video.src.comments import CommentList
from video.src.index import YoutubeVideo, index_new_video


class Scanner:
    """scan index and filesystem"""

    VIDEOS: str = EnvironmentSettings.MEDIA_DIR

    def __init__(self, task=False) -> None:
        self.task = task
        self.to_delete: set[str] = set()
        self.to_index: set[str] = set()

    def scan(self) -> None:
        """scan the filesystem"""
        downloaded: set[str] = self._get_downloaded()
        indexed: set[str] = self._get_indexed()
        self.to_index = downloaded - indexed
        self.to_delete = indexed - downloaded

    def _get_downloaded(self) -> set[str]:
        """get downloaded ids"""
        if self.task:
            self.task.send_progress(["Scan your filesystem for videos."])

        downloaded: set = set()
        channels = ignore_filelist(os.listdir(self.VIDEOS))
        for channel in channels:
            folder = os.path.join(self.VIDEOS, channel)
            files = ignore_filelist(os.listdir(folder))
            downloaded.update({i.split(".")[0] for i in files})

        return downloaded

    def _get_indexed(self) -> set:
        """get all indexed ids"""
        if self.task:
            self.task.send_progress(["Get all videos indexed."])

        data = {"query": {"match_all": {}}, "_source": ["youtube_id"]}
        response = IndexPaginate("ta_video", data).get_results()
        return {i["youtube_id"] for i in response}

    def apply(self) -> None:
        """apply all changes"""
        self.delete()
        self.index()

    def delete(self) -> None:
        """delete videos from index"""
        if not self.to_delete:
            print("nothing to delete")
            return

        if self.task:
            self.task.send_progress(
                [f"Remove {len(self.to_delete)} videos from index."]
            )

        for youtube_id in self.to_delete:
            YoutubeVideo(youtube_id).delete_media_file()

    def index(self) -> None:
        """index new"""
        if not self.to_index:
            print("nothing to index")
            return

        total = len(self.to_index)
        for idx, youtube_id in enumerate(self.to_index):
            if self.task:
                self.task.send_progress(
                    message_lines=[
                        f"Index missing video {youtube_id}, {idx + 1}/{total}"
                    ],
                    progress=(idx + 1) / total,
                )
            index_new_video(youtube_id)

        comment_list = CommentList(task=self.task)
        comment_list.add(video_ids=list(self.to_index))
        comment_list.index()
