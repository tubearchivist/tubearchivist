"""
Functionality:
- scan the filesystem to delete or index
"""

import os

from home.src.es.connect import ElasticWrap, IndexPaginate
from home.src.index.comments import CommentList
from home.src.index.video import YoutubeVideo, index_new_video
from home.src.ta.helper import ignore_filelist
from home.src.ta.settings import EnvironmentSettings


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
        self.url_fix()

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

    def url_fix(self) -> None:
        """
        update path v0.3.6 to v0.3.7
        fix url not matching channel-videoid pattern
        """
        bool_must = (
            "doc['media_url'].value == "
            + "(doc['channel.channel_id'].value + '/' + "
            + "doc['youtube_id'].value) + '.mp4'"
        )
        to_update = (
            "ctx._source['media_url'] = "
            + "ctx._source.channel['channel_id'] + '/' + "
            + "ctx._source['youtube_id'] + '.mp4'"
        )
        data = {
            "query": {
                "bool": {
                    "must_not": [{"script": {"script": {"source": bool_must}}}]
                }
            },
            "script": {"source": to_update},
        }
        response, _ = ElasticWrap("ta_video/_update_by_query").post(data=data)
        updated = response.get("updates")
        if updated:
            print(f"updated {updated} bad media_url")
            if self.task:
                self.task.send_progress(
                    [f"Updated {updated} wrong media urls."]
                )
