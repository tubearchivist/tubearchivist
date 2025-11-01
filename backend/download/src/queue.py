"""
Functionality:
- handle download queue
- linked with ta_dowload index
"""

import json
from datetime import datetime
from zoneinfo import ZoneInfo

from appsettings.src.config import AppConfig
from channel.src.index import YoutubeChannel
from channel.src.remote_query import get_last_channel_videos
from common.src.env_settings import EnvironmentSettings
from common.src.es_connect import ElasticWrap, IndexPaginate
from common.src.helper import (
    get_channels,
    get_duration_str,
    is_shorts,
    rand_sleep,
)
from common.src.urlparser import ParsedURLType
from download.src.queue_interact import PendingInteract
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
        channels = get_channels(subscribed_only=False)

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


class PendingList(PendingIndex):
    """manage the pending videos list"""

    yt_obs = {
        "noplaylist": True,
        "writethumbnail": True,
        "simulate": True,
        "check_formats": None,
    }

    def __init__(
        self,
        youtube_ids: list[ParsedURLType],
        task=None,
        auto_start=False,
        flat=False,
        force=False,
    ):
        super().__init__()
        self.config = AppConfig().config
        self.youtube_ids = youtube_ids
        self.task = task
        self.auto_start = auto_start
        self.flat = flat
        self.force = force
        self.to_skip = False
        self.missing_videos: list[dict] = []
        self.added = 0

    def parse_url_list(self, status="pending") -> int:
        """extract youtube ids from list"""
        self.get_download()
        self.get_indexed()
        self.get_channels()
        total = len(self.youtube_ids)
        for idx, entry in enumerate(self.youtube_ids, start=1):
            if self.task:
                self.task.send_progress(
                    message_lines=[f"Extracting URL {idx}/{total}"],
                    progress=idx / total,
                )

            self._process_entry(entry, idx, total)

            if self.missing_videos:
                self.added += self.add_to_pending(status)
                self.missing_videos = []

            if self.task and self.task.is_stopped():
                break

            rand_sleep(self.config)

        return self.added

    def _process_entry(self, entry: ParsedURLType, idx: int, total: int):
        """process single entry from url list"""
        if entry["type"] == "video":
            to_add = self._add_video(entry["url"], entry["vid_type"])
            if to_add:
                self._notify_add(
                    item_type="video",
                    name=to_add["title"],
                    idx=idx,
                    total=total,
                )

        elif entry["type"] == "channel":
            self._parse_channel(entry)
        elif entry["type"] == "playlist":
            self._parse_playlist(entry["url"], entry.get("limit"))
        else:
            raise ValueError(f"invalid url_type: {entry}")

    def _add_video(self, url, vid_type) -> dict | None:
        """add video to list"""
        if self.auto_start and url in set(
            i["youtube_id"] for i in self.all_pending
        ):
            PendingInteract(youtube_id=url, status="priority").update_status()
            return None

        if not self.force and (
            url in self.missing_videos or url in self.to_skip
        ):
            print(f"{url}: skipped adding already indexed video to download.")
            return None

        if self.force and url in self.all_ignored or url in self.all_pending:
            print(f"{url}: skipped adding force video already in queue.")
            return None

        to_add = self._parse_video(url, vid_type)
        if to_add:
            self.missing_videos.append(to_add)

        return to_add

    def _parse_channel(self, entry) -> None:
        """parse channel"""
        url = entry["url"]
        vid_type = entry["vid_type"]
        if isinstance(vid_type, str):
            # lookup enum
            vid_type = getattr(VideoTypeEnum, vid_type.upper())

        limit = entry.get("limit")
        video_results = get_last_channel_videos(
            channel_id=url,
            config=self.config,
            limit=limit,
            query_filter=vid_type,
        )
        if not video_results:
            print(f"{url}: no videos to add from channel, skipping")
            return

        channel_handler = YoutubeChannel(url)
        channel_handler.build_json(upload=False)
        if not channel_handler.json_data:
            print(f"{url}: channel metadata extraction failed, skipping")
            return

        total = len(video_results)
        for idx, video_data in enumerate(video_results, start=1):
            to_add = self._parse_channel_video(
                video_data, vid_type, channel_handler.json_data
            )
            if self.task and self.task.is_stopped():
                break

            if not to_add:
                continue

            self.missing_videos.append(to_add)
            self._notify_add(
                item_type="channel",
                name=channel_handler.json_data["channel_name"],
                idx=idx,
                total=total,
            )

    def _parse_channel_video(
        self, video_data, vid_type, channel_json
    ) -> dict | None:
        """parse video of channel"""
        video_id = video_data["id"]
        if video_id in self.to_skip:
            return None

        # fallback
        channel_name = channel_json["channel_name"]
        channel_id = channel_json["channel_id"]

        if self.flat:
            if not video_data.get("channel"):
                video_data["channel"] = channel_name

            if not video_data.get("channel_id"):
                video_data["channel_id"] = channel_id

            to_add = self._parse_entry(
                youtube_id=video_id,
                video_data=video_data,
            )
        else:
            to_add = self._parse_video(video_id, vid_type)

        return to_add

    def _parse_playlist(self, url: str, limit: int | None):
        """fast parse playlist"""
        playlist = YoutubePlaylist(url)
        playlist.update_playlist()
        if not playlist.youtube_meta:
            print(f"{url}: playlist metadata extraction failed, skipping")
            return

        video_results = playlist.youtube_meta["entries"]
        if limit:
            video_results = video_results[:limit]

        total = len(video_results)
        for idx, video_data in enumerate(video_results, start=1):
            video_id = video_data["id"]
            if video_id in self.to_skip:
                continue

            if self.task and self.task.is_stopped():
                break

            if self.flat:
                if not video_data.get("channel"):
                    video_data["channel"] = playlist.youtube_meta["channel"]

                if not video_data.get("channel_id"):
                    channel_id = playlist.youtube_meta["channel_id"]
                    video_data["channel_id"] = channel_id

                to_add = self._parse_entry(video_id, video_data)
            else:
                to_add = self._parse_video(video_id, vid_type=None)

            if not to_add:
                continue

            self.missing_videos.append(to_add)
            self._notify_add(
                item_type="playlist",
                name=playlist.json_data["playlist_name"],
                idx=idx,
                total=total,
            )

    def _parse_video(self, url: str, vid_type) -> dict | None:
        """parse video when not flat, fetch from YT"""
        video = YoutubeVideo(youtube_id=url)
        video.get_from_youtube()

        if not video.youtube_meta:
            print(f"{url}: video metadata extraction failed, skipping")
            if self.task:
                self.task.send_progress(
                    message_lines=[
                        "Video extraction failed.",
                        f"{video.error}",
                    ],
                    level="error",
                )
            return None

        expected_keys = {"id", "title", "channel", "channel_id"}
        if not set(video.youtube_meta.keys()).issuperset(expected_keys):
            print(f"{url}: video metadata extraction incomplete, skipping")
            if self.task:
                self.task.send_progress(
                    message_lines=[
                        "Video extraction failed.",
                        "Metadata extraction incomplete.",
                    ],
                    level="error",
                )
            return None

        video.youtube_meta["vid_type"] = vid_type
        to_add = self._parse_entry(
            youtube_id=url,
            video_data=video.youtube_meta,
        )
        if not to_add:
            return None

        ThumbManager(item_id=url).download_video_thumb(to_add["vid_thumb_url"])
        rand_sleep(self.config)

        return to_add

    def _parse_entry(
        self,
        youtube_id: str,
        video_data: dict,
    ) -> dict | None:
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
            "vid_thumb_url": self._extract_thumb(video_data),
            "duration": get_duration_str(video_data.get("duration", 0)),
            "published": self._extract_published(video_data),
            "timestamp": int(datetime.now().timestamp()),
            "vid_type": self._extract_vid_type(video_data),
            "channel_name": video_data["channel"],
            "channel_id": video_data["channel_id"],
            "channel_indexed": video_data["channel_id"] in self.all_channels,
        }

        return to_add

    def _extract_thumb(self, video_data) -> str | None:
        """extract thumb"""
        if "thumbnail" in video_data:
            return video_data["thumbnail"]

        if video_data.get("thumbnails"):
            return video_data["thumbnails"][-1]["url"]

        return None

    @staticmethod
    def _extract_published(video_data) -> str | int | None:
        """build published date or timestamp"""
        timestamp = video_data.get("timestamp")
        if timestamp:
            return timestamp

        upload_date = video_data.get("upload_date")
        if upload_date:
            upload_date_time = datetime.strptime(upload_date, "%Y%m%d")
            return upload_date_time.replace(
                tzinfo=ZoneInfo(EnvironmentSettings.TZ)
            ).timestamp()

        return None

    def _extract_vid_type(self, video_data) -> str:
        """build vid type"""
        if (
            "vid_type" in video_data
            and video_data["vid_type"]
            and str(video_data["vid_type"]) in VideoTypeEnum.values_known()
        ):
            return VideoTypeEnum(video_data["vid_type"]).value

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
        response, status_code = ElasticWrap("_bulk").post(
            query_str, ndjson=True
        )
        if status_code not in [200, 201]:
            print(response)
            self._notify_fail(status_code)
        elif response.get("errors", False):
            failed_video_ids = []
            for item in response.get("items", []):
                action, result = next(iter(item.items()))
                if "error" in result:
                    failed_video_ids.append(result.get("_id"))

            failed_video_ids_str = ",".join(failed_video_ids)
            self._notify_fail(status_code, failed_video_ids_str)
        else:
            self._notify_done(total)

        return len(self.missing_videos)

    def _notify_add(
        self, item_type: str, name: str, idx: int, total: int
    ) -> None:
        """notify"""
        if not self.task:
            return

        if self.flat:
            lines = [
                f"Bulk extracting {item_type.title()}: '{name}'.",
                f"Fast adding item {idx}/{total}.",
            ]
        else:
            lines = [
                f"Full extracting {item_type.title()}: '{name}'",
                f"Parsing item {idx}/{total}.",
            ]

        self.task.send_progress(
            message_lines=lines,
            progress=idx / total,
        )

    def _notify_empty(self):
        """notify nothing to add"""
        if not self.task:
            return

        self.task.send_progress(
            message_lines=[
                "Extracting videos completed.",
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

    def _notify_fail(self, status_code, failed_video_ids=None):
        """failed to add"""
        if not self.task:
            return

        message_lines = [
            "Adding extracted videos failed.",
            f"Status code: {status_code}",
        ]

        if failed_video_ids:
            message_lines.append(f"Failed Videos: {failed_video_ids}")

        self.task.send_progress(
            message_lines=message_lines,
            level="error",
        )
