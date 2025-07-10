"""
Functionality:
- handle download queue
- linked with ta_dowload index
"""

import json
from datetime import datetime

from appsettings.src.config import AppConfig
from channel.src.index import YoutubeChannel
from common.src.es_connect import ElasticWrap, IndexPaginate
from common.src.helper import get_duration_str, is_shorts, rand_sleep
from download.src.subscriptions import ChannelSubscription
from download.src.thumbnails import ThumbManager
from playlist.src.index import YoutubePlaylist
from video.src.constants import VideoTypeEnum
from video.src.index import YoutubeVideo


class PendingIndex:
    """base class holding all export methods"""

    def __init__(self):
        self.all_pending = False
        self.all_ignored = False
        self.all_videos = False
        self.all_channels = False
        self.channel_overwrites = False
        self.video_overwrites = False
        self.to_skip = False

    def get_download(self):
        """get a list of all pending videos in ta_download"""
        data = {
            "query": {"match_all": {}},
            "sort": [{"timestamp": {"order": "asc"}}],
        }
        all_results = IndexPaginate("ta_download", data).get_results()

        self.all_pending = []
        self.all_ignored = []
        self.to_skip = []

        for result in all_results:
            self.to_skip.append(result["youtube_id"])
            if result["status"] == "pending":
                self.all_pending.append(result)
            elif result["status"] == "ignore":
                self.all_ignored.append(result)

    def get_indexed(self):
        """get a list of all videos indexed"""
        data = {
            "query": {"match_all": {}},
            "sort": [{"published": {"order": "desc"}}],
        }
        self.all_videos = IndexPaginate("ta_video", data).get_results()
        for video in self.all_videos:
            self.to_skip.append(video["youtube_id"])

    def get_channels(self):
        """get a list of all channels indexed"""
        self.all_channels = []
        self.channel_overwrites = {}
        data = {
            "query": {"match_all": {}},
            "sort": [{"channel_id": {"order": "asc"}}],
        }
        channels = IndexPaginate("ta_channel", data).get_results()

        for channel in channels:
            channel_id = channel["channel_id"]
            self.all_channels.append(channel_id)
            if channel.get("channel_overwrites"):
                self.channel_overwrites.update(
                    {channel_id: channel.get("channel_overwrites")}
                )

        self._map_overwrites()

    def _map_overwrites(self):
        """map video ids to channel ids overwrites"""
        self.video_overwrites = {}
        for video in self.all_pending:
            video_id = video["youtube_id"]
            channel_id = video["channel_id"]
            overwrites = self.channel_overwrites.get(channel_id, False)
            if overwrites:
                self.video_overwrites.update({video_id: overwrites})


class PendingInteract:
    """interact with items in download queue"""

    def __init__(self, youtube_id=False, status=False):
        self.youtube_id = youtube_id
        self.status = status

    def delete_item(self):
        """delete single item from pending"""
        path = f"ta_download/_doc/{self.youtube_id}"
        _, _ = ElasticWrap(path).delete(refresh=True)

    def delete_bulk(self, channel_id: str | None, vid_type: str | None):
        """delete all matching item by status"""
        must_list = [{"term": {"status": {"value": self.status}}}]
        if channel_id:
            must_list.append({"term": {"channel_id": {"value": channel_id}}})

        if vid_type:
            must_list.append({"term": {"vid_type": {"value": vid_type}}})

        data = {"query": {"bool": {"must": must_list}}}

        path = "ta_download/_delete_by_query?refresh=true"
        _, _ = ElasticWrap(path).post(data=data)

    def update_bulk(
        self, channel_id: str | None, vid_type: str | None, new_status: str
    ):
        """update status in bulk"""
        must_list = [{"term": {"status": {"value": self.status}}}]
        if channel_id:
            must_list.append({"term": {"channel_id": {"value": channel_id}}})

        if vid_type:
            must_list.append({"term": {"vid_type": {"value": vid_type}}})

        if new_status == "priority":
            source = """
            ctx._source.status = 'pending';
            ctx._source.auto_start = true;
            ctx._source.message = null;
            """
        else:
            source = f"ctx._source.status = '{new_status}'"

        data = {
            "query": {"bool": {"must": must_list}},
            "script": {"source": source, "lang": "painless"},
        }

        path = "ta_download/_update_by_query?refresh=true"
        _, _ = ElasticWrap(path).post(data)

    def update_status(self):
        """update status of pending item"""
        if self.status == "priority":
            data = {
                "doc": {
                    "status": "pending",
                    "auto_start": True,
                    "message": None,
                }
            }
        else:
            data = {"doc": {"status": self.status}}

        path = f"ta_download/_update/{self.youtube_id}/?refresh=true"
        _, _ = ElasticWrap(path).post(data=data)

    def get_item(self):
        """return pending item dict"""
        path = f"ta_download/_doc/{self.youtube_id}"
        response, status_code = ElasticWrap(path).get()
        return response["_source"], status_code

    def get_channel(self):
        """
        get channel metadata from queue to not depend on channel to be indexed
        """
        data = {
            "size": 1,
            "query": {"term": {"channel_id": {"value": self.youtube_id}}},
        }
        response, _ = ElasticWrap("ta_download/_search").get(data=data)
        hits = response["hits"]["hits"]
        if not hits:
            channel_name = "NA"
        else:
            channel_name = hits[0]["_source"].get("channel_name", "NA")

        return {
            "channel_id": self.youtube_id,
            "channel_name": channel_name,
        }


class PendingList(PendingIndex):
    """manage the pending videos list"""

    yt_obs = {
        "noplaylist": True,
        "writethumbnail": True,
        "simulate": True,
        "check_formats": None,
    }

    def __init__(
        self, youtube_ids=False, task=False, auto_start=False, flat=False
    ):
        super().__init__()
        self.config = AppConfig().config
        self.youtube_ids = youtube_ids
        self.task = task
        self.auto_start = auto_start
        self.flat = flat
        self.to_skip = False
        self.missing_videos = []

    def parse_url_list(self):
        """extract youtube ids from list"""
        self.get_download()
        self.get_indexed()
        self.get_channels()
        total = len(self.youtube_ids)
        for idx, entry in enumerate(self.youtube_ids):
            self._process_entry(entry)
            rand_sleep(self.config)
            if not self.task:
                continue

            self.task.send_progress(
                message_lines=[f"Extracting items {idx + 1}/{total}"],
                progress=(idx + 1) / total,
            )

    def _process_entry(self, entry: dict):
        """process single entry from url list"""
        if entry["type"] == "video":
            self._add_video(entry["url"], entry["vid_type"])
        elif entry["type"] == "channel":
            self._parse_channel(entry["url"], entry["vid_type"])
        elif entry["type"] == "playlist":
            self._parse_playlist(entry["url"])
        else:
            raise ValueError(f"invalid url_type: {entry}")

    def _add_video(self, url, vid_type):
        """add video to list"""
        if self.auto_start and url in set(
            i["youtube_id"] for i in self.all_pending
        ):
            PendingInteract(youtube_id=url, status="priority").update_status()
            return

        if url in self.missing_videos or url in self.to_skip:
            print(f"{url}: skipped adding already indexed video to download.")
        else:
            to_add = self._parse_video(url, vid_type)
            if to_add:
                self.missing_videos.append(to_add)

    def _parse_channel(self, url, vid_type):
        """parse channel"""
        query_filter = getattr(VideoTypeEnum, vid_type.upper())
        video_results = ChannelSubscription().get_last_youtube_videos(
            url, limit=False, query_filter=query_filter
        )
        channel_handler = YoutubeChannel(url)
        channel_handler.build_json(upload=False)

        for video_data in video_results:
            video_id = video_data["id"]
            if video_id in self.to_skip:
                continue

            if self.flat:
                if not video_data.get("channel"):
                    channel_name = channel_handler.json_data["channel_name"]
                    video_data["channel"] = channel_name

                if not video_data.get("channel_id"):
                    channel_id = channel_handler.json_data["channel_id"]
                    video_data["channel_id"] = channel_id

                to_add = self._parse_entry(
                    youtube_id=video_id, video_data=video_data
                )
            else:
                to_add = self._parse_video(video_id, vid_type)

            if to_add:
                self.missing_videos.append(to_add)

    def _parse_playlist(self, url):
        """fast parse playlist"""
        playlist = YoutubePlaylist(url)
        playlist.get_from_youtube()
        video_results = playlist.youtube_meta["entries"]

        for video_data in video_results:
            video_id = video_data["id"]
            if video_id in self.to_skip:
                continue

            if self.flat:
                if not video_data.get("channel"):
                    video_data["channel"] = playlist.youtube_meta["channel"]

                if not video_data.get("channel_id"):
                    channel_id = playlist.youtube_meta["channel_id"]
                    video_data["channel_id"] = channel_id

                to_add = self._parse_entry(video_id, video_data)
            else:
                to_add = self._parse_video(video_id, vid_type=None)

            if to_add:
                self.missing_videos.append(to_add)

    def _parse_video(self, url, vid_type):
        """parse video"""
        video = YoutubeVideo(youtube_id=url)
        video.get_from_youtube()

        video_data = video.youtube_meta
        video_data["vid_type"] = vid_type
        to_add = self._parse_entry(youtube_id=url, video_data=video_data)
        rand_sleep(self.config)

        return to_add

    def _parse_entry(self, youtube_id: str, video_data: dict) -> dict | None:
        """parse entry"""
        if video_data.get("id") != youtube_id:
            # skip premium videos with different id or redirects
            print(f"{youtube_id}: skipping redirect, id not matching")
            return None

        if video_data.get("live_status") in ["is_upcoming", "is_live"]:
            print(f"{youtube_id}: skip is_upcoming or is_live")
            return None

        to_add = {
            "youtube_id": video_data["id"],
            "title": video_data["title"],
            "vid_thumb_url": self.__extract_thumb(video_data),
            "duration": get_duration_str(video_data.get("duration", 0)),
            "published": self.__extract_published(video_data),
            "timestamp": int(datetime.now().timestamp()),
            "vid_type": self.__extract_vid_type(video_data),
            "channel_name": video_data["channel"],
            "channel_id": video_data["channel_id"],
            "channel_indexed": video_data["channel_id"] in self.all_channels,
        }
        thumb_url = to_add["vid_thumb_url"]
        ThumbManager(to_add["youtube_id"]).download_video_thumb(thumb_url)

        return to_add

    def __extract_thumb(self, video_data) -> str | None:
        """extract thumb"""
        if "thumbnail" in video_data:
            return video_data["thumbnail"]

        if "thumbnails" in video_data:
            return video_data["thumbnails"][-1]["url"]

        return None

    def __extract_published(self, video_data) -> str | int | None:
        """build published date or timestamp"""
        timestamp = video_data.get("timestamp")
        if timestamp:
            return timestamp

        upload_date = video_data.get("upload_date")
        if not upload_date:
            return None

        upload_date_time = datetime.strptime(upload_date, "%Y%m%d")
        published = upload_date_time.strftime("%Y-%m-%d")

        return published

    def __extract_vid_type(self, video_data) -> str:
        """build vid type"""
        if "vid_type" in video_data:
            return video_data["vid_type"]

        if video_data.get("live_status") == "was_live":
            return VideoTypeEnum.STREAMS.value

        if video_data.get("width", 0) > video_data.get("height", 0):
            return VideoTypeEnum.VIDEOS.value

        duration = video_data.get("duration")
        if duration and isinstance(duration, int):
            if duration > 3 * 60:
                return VideoTypeEnum.VIDEOS.value

        if is_shorts(video_data["id"]):
            return VideoTypeEnum.SHORTS.value

        return VideoTypeEnum.VIDEOS.value

    def add_to_pending(self, status="pending") -> int:
        """add missing videos to pending list"""

        total = len(self.missing_videos)

        if not self.missing_videos:
            self._notify_empty()
            return 0

        self._notify_start(total)
        bulk_list = []
        for video_entry in self.missing_videos:
            video_entry.update(
                {
                    "status": status,
                    "auto_start": self.auto_start,
                }
            )
            video_id = video_entry["youtube_id"]
            action = {"index": {"_index": "ta_download", "_id": video_id}}
            bulk_list.append(json.dumps(action))
            bulk_list.append(json.dumps(video_entry))

        # add last newline
        bulk_list.append("\n")
        query_str = "\n".join(bulk_list)
        _, status_code = ElasticWrap("_bulk").post(query_str, ndjson=True)
        if status_code != 200:
            self._notify_fail(status_code)
        else:
            self._notify_done(total)

        return len(self.missing_videos)

    def _notify_empty(self):
        """notify nothing to add"""
        if not self.task:
            return

        self.task.send_progress(
            message_lines=[
                "Extractinc videos completed.",
                "No new videos found to add.",
            ]
        )

    def _notify_start(self, total):
        """send notification for adding videos to download queue"""
        if not self.task:
            return

        self.task.send_progress(
            message_lines=[
                "Adding new videos to download queue.",
                f"Bulk adding {total} videos",
            ]
        )

    def _notify_done(self, total):
        """send done notification"""
        if not self.task:
            return

        self.task.send_progress(
            message_lines=[
                "Adding new videos to the queue completed.",
                f"Added {total} videos.",
            ]
        )

    def _notify_fail(self, status_code):
        """failed to add"""
        if not self.task:
            return

        self.task.send_progress(
            message_lines=[
                "Adding extracted videos failed.",
                f"Status code: {status_code}",
            ]
        )
