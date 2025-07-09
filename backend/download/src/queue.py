"""
Functionality:
- handle download queue
- linked with ta_dowload index
"""

from datetime import datetime

from appsettings.src.config import AppConfig
from common.src.es_connect import ElasticWrap, IndexPaginate
from common.src.helper import get_duration_str, is_shorts, rand_sleep
from download.src.subscriptions import ChannelSubscription
from download.src.thumbnails import ThumbManager
from download.src.yt_dlp_base import YtWrap
from playlist.src.index import YoutubePlaylist
from video.src.constants import VideoTypeEnum


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

    def __init__(self, youtube_ids=False, task=False):
        super().__init__()
        self.config = AppConfig().config
        self.youtube_ids = youtube_ids
        self.task = task
        self.to_skip = False
        self.missing_videos = False

    def parse_url_list(self, auto_start=False):
        """extract youtube ids from list"""
        self.missing_videos = []
        self.get_download()
        self.get_indexed()
        total = len(self.youtube_ids)
        for idx, entry in enumerate(self.youtube_ids):
            self._process_entry(entry, auto_start=auto_start)
            if not self.task:
                continue

            self.task.send_progress(
                message_lines=[f"Extracting items {idx + 1}/{total}"],
                progress=(idx + 1) / total,
            )

    def _process_entry(self, entry, auto_start=False):
        """process single entry from url list"""
        vid_type = self._get_vid_type(entry)
        if entry["type"] == "video":
            self._add_video(entry["url"], vid_type, auto_start=auto_start)
        elif entry["type"] == "channel":
            self._parse_channel(entry["url"], vid_type)
        elif entry["type"] == "playlist":
            self._parse_playlist(entry["url"])
        else:
            raise ValueError(f"invalid url_type: {entry}")

    @staticmethod
    def _get_vid_type(entry):
        """add vid type enum if available"""
        vid_type_str = entry.get("vid_type")
        if not vid_type_str:
            return VideoTypeEnum.UNKNOWN

        return VideoTypeEnum(vid_type_str)

    def _add_video(self, url, vid_type, auto_start=False):
        """add video to list"""
        if auto_start and url in set(
            i["youtube_id"] for i in self.all_pending
        ):
            PendingInteract(youtube_id=url, status="priority").update_status()
            return

        if url not in self.missing_videos and url not in self.to_skip:
            self.missing_videos.append((url, vid_type))
        else:
            print(f"{url}: skipped adding already indexed video to download.")

    def _parse_channel(self, url, vid_type):
        """add all videos of channel to list"""
        video_results = ChannelSubscription().get_last_youtube_videos(
            url, limit=False, query_filter=vid_type
        )
        for video_id, _, vid_type in video_results:
            self._add_video(video_id, vid_type)

    def _parse_playlist(self, url):
        """add all videos of playlist to list"""
        playlist = YoutubePlaylist(url)
        is_active = playlist.update_playlist()
        if not is_active:
            message = f"{playlist.youtube_id}: failed to extract metadata"
            print(message)
            raise ValueError(message)

        entries = playlist.json_data["playlist_entries"]
        to_add = [i["youtube_id"] for i in entries if not i["downloaded"]]
        if not to_add:
            return

        for video_id in to_add:
            # match vid_type later
            self._add_video(video_id, VideoTypeEnum.UNKNOWN)

    def add_to_pending(self, status="pending", auto_start=False):
        """add missing videos to pending list"""
        self.get_channels()

        total = len(self.missing_videos)
        videos_added = []
        for idx, (youtube_id, vid_type) in enumerate(self.missing_videos):
            if self.task and self.task.is_stopped():
                break

            print(f"{youtube_id}: [{idx + 1}/{total}]: add to queue")
            self._notify_add(idx, total)
            video_details = self.get_youtube_details(youtube_id, vid_type)
            if not video_details:
                rand_sleep(self.config)
                continue

            video_details.update(
                {
                    "status": status,
                    "auto_start": auto_start,
                }
            )

            url = video_details["vid_thumb_url"]
            ThumbManager(youtube_id).download_video_thumb(url)
            es_url = f"ta_download/_doc/{youtube_id}"
            _, _ = ElasticWrap(es_url).put(video_details)
            videos_added.append(youtube_id)

            if idx != total:
                rand_sleep(self.config)

        return videos_added

    def _notify_add(self, idx, total):
        """send notification for adding videos to download queue"""
        if not self.task:
            return

        self.task.send_progress(
            message_lines=[
                "Adding new videos to download queue.",
                f"Extracting items {idx + 1}/{total}",
            ],
            progress=(idx + 1) / total,
        )

    def get_youtube_details(self, youtube_id, vid_type=VideoTypeEnum.VIDEOS):
        """get details from youtubedl for single pending video"""
        vid = YtWrap(self.yt_obs, self.config).extract(youtube_id)
        if not vid:
            return False

        if vid.get("id") != youtube_id:
            # skip premium videos with different id
            print(f"{youtube_id}: skipping premium video, id not matching")
            return False
        # stop if video is streaming live now
        if vid["live_status"] in ["is_upcoming", "is_live"]:
            print(f"{youtube_id}: skip is_upcoming or is_live")
            return False

        if vid["live_status"] == "was_live":
            vid_type = VideoTypeEnum.STREAMS
        else:
            if self._check_shorts(vid):
                vid_type = VideoTypeEnum.SHORTS
            else:
                vid_type = VideoTypeEnum.VIDEOS

        if not vid.get("channel"):
            print(f"{youtube_id}: skip video not part of channel")
            return False

        return self._parse_youtube_details(vid, vid_type)

    @staticmethod
    def _check_shorts(vid):
        """check if vid is shorts video"""
        if vid["width"] > vid["height"]:
            return False

        duration = vid.get("duration")
        if duration and isinstance(duration, int):
            if duration > 3 * 60:
                return False

        return is_shorts(vid["id"])

    def _parse_youtube_details(self, vid, vid_type=VideoTypeEnum.VIDEOS):
        """parse response"""
        vid_id = vid.get("id")

        # build dict
        youtube_details = {
            "youtube_id": vid_id,
            "channel_name": vid["channel"],
            "vid_thumb_url": vid["thumbnail"],
            "title": vid["title"],
            "channel_id": vid["channel_id"],
            "duration": get_duration_str(vid["duration"]),
            "published": self._build_published(vid),
            "timestamp": int(datetime.now().timestamp()),
            "vid_type": vid_type.value,
            "channel_indexed": vid["channel_id"] in self.all_channels,
        }

        return youtube_details

    @staticmethod
    def _build_published(vid):
        """build published date or timestamp"""
        timestamp = vid["timestamp"]
        if timestamp:
            return timestamp

        upload_date = vid["upload_date"]
        upload_date_time = datetime.strptime(upload_date, "%Y%m%d")
        published = upload_date_time.strftime("%Y-%m-%d")

        return published
