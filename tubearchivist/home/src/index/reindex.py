"""
functionality:
- periodically refresh documents
- index and update in es
"""

import json
import os
from datetime import datetime
from time import sleep
from typing import Callable, TypedDict

from home.models import CustomPeriodicTask
from home.src.download.subscriptions import ChannelSubscription
from home.src.download.thumbnails import ThumbManager
from home.src.download.yt_dlp_base import CookieHandler
from home.src.es.connect import ElasticWrap, IndexPaginate
from home.src.index.channel import YoutubeChannel
from home.src.index.comments import Comments
from home.src.index.playlist import YoutubePlaylist
from home.src.index.video import YoutubeVideo
from home.src.ta.config import AppConfig
from home.src.ta.settings import EnvironmentSettings
from home.src.ta.ta_redis import RedisQueue


class ReindexConfigType(TypedDict):
    """represents config type"""

    index_name: str
    queue_name: str
    active_key: str
    refresh_key: str


class ReindexBase:
    """base config class for reindex task"""

    REINDEX_CONFIG: dict[str, ReindexConfigType] = {
        "video": {
            "index_name": "ta_video",
            "queue_name": "reindex:ta_video",
            "active_key": "active",
            "refresh_key": "vid_last_refresh",
        },
        "channel": {
            "index_name": "ta_channel",
            "queue_name": "reindex:ta_channel",
            "active_key": "channel_active",
            "refresh_key": "channel_last_refresh",
        },
        "playlist": {
            "index_name": "ta_playlist",
            "queue_name": "reindex:ta_playlist",
            "active_key": "playlist_active",
            "refresh_key": "playlist_last_refresh",
        },
    }

    MULTIPLY = 1.2
    DAYS3 = 60 * 60 * 24 * 3

    def __init__(self):
        self.config = AppConfig().config
        self.now = int(datetime.now().timestamp())

    def populate(self, all_ids, reindex_config: ReindexConfigType):
        """add all to reindex ids to redis queue"""
        if not all_ids:
            return

        RedisQueue(queue_name=reindex_config["queue_name"]).add_list(all_ids)


class ReindexPopulate(ReindexBase):
    """add outdated and recent documents to reindex queue"""

    INTERVAL_DEFAIULT: int = 90

    def __init__(self):
        super().__init__()
        self.interval = self.INTERVAL_DEFAIULT

    def get_interval(self) -> None:
        """get reindex days interval from task"""
        try:
            task = CustomPeriodicTask.objects.get(name="check_reindex")
        except CustomPeriodicTask.DoesNotExist:
            return

        task_config = task.task_config
        if task_config.get("days"):
            self.interval = task_config.get("days")

    def add_recent(self) -> None:
        """add recent videos to refresh"""
        gte = datetime.fromtimestamp(self.now - self.DAYS3).date().isoformat()
        must_list = [
            {"term": {"active": {"value": True}}},
            {"range": {"published": {"gte": gte}}},
        ]
        data = {
            "size": 10000,
            "query": {"bool": {"must": must_list}},
            "sort": [{"published": {"order": "desc"}}],
        }
        response, _ = ElasticWrap("ta_video/_search").get(data=data)
        hits = response["hits"]["hits"]
        if not hits:
            return

        all_ids = [i["_source"]["youtube_id"] for i in hits]
        reindex_config: ReindexConfigType = self.REINDEX_CONFIG["video"]
        self.populate(all_ids, reindex_config)

    def add_outdated(self) -> None:
        """add outdated documents"""
        for reindex_config in self.REINDEX_CONFIG.values():
            total_hits = self._get_total_hits(reindex_config)
            daily_should = self._get_daily_should(total_hits)
            all_ids = self._get_outdated_ids(reindex_config, daily_should)
            self.populate(all_ids, reindex_config)

    @staticmethod
    def _get_total_hits(reindex_config: ReindexConfigType) -> int:
        """get total hits from index"""
        index_name = reindex_config["index_name"]
        active_key = reindex_config["active_key"]
        data = {
            "query": {"term": {active_key: {"value": True}}},
            "_source": False,
        }
        total = IndexPaginate(index_name, data, keep_source=True).get_results()

        return len(total)

    def _get_daily_should(self, total_hits: int) -> int:
        """calc how many should reindex daily"""
        daily_should = int((total_hits // self.interval + 1) * self.MULTIPLY)
        if daily_should >= 10000:
            daily_should = 9999

        return daily_should

    def _get_outdated_ids(
        self, reindex_config: ReindexConfigType, daily_should: int
    ) -> list[str]:
        """get outdated from index_name"""
        index_name = reindex_config["index_name"]
        refresh_key = reindex_config["refresh_key"]
        now_lte = str(self.now - self.interval * 24 * 60 * 60)
        must_list = [
            {"match": {reindex_config["active_key"]: True}},
            {"range": {refresh_key: {"lte": now_lte}}},
        ]
        data = {
            "size": daily_should,
            "query": {"bool": {"must": must_list}},
            "sort": [{refresh_key: {"order": "asc"}}],
            "_source": False,
        }
        response, _ = ElasticWrap(f"{index_name}/_search").get(data=data)

        all_ids = [i["_id"] for i in response["hits"]["hits"]]
        return all_ids


class ReindexManual(ReindexBase):
    """
    manually add ids to reindex queue from API
    data_example = {
        "video": ["video1", "video2", "video3"],
        "channel": ["channel1", "channel2", "channel3"],
        "playlist": ["playlist1", "playlist2"],
    }
    extract_videos to also reindex all videos of channel/playlist
    """

    def __init__(self, extract_videos=False):
        super().__init__()
        self.extract_videos = extract_videos
        self.data = False

    def extract_data(self, data) -> None:
        """process data"""
        self.data = data
        for key, values in self.data.items():
            reindex_config = self.REINDEX_CONFIG.get(key)
            if not reindex_config:
                print(f"reindex type {key} not valid")
                raise ValueError

            self.process_index(reindex_config, values)

    def process_index(
        self, index_config: ReindexConfigType, values: list[str]
    ) -> None:
        """process values per index"""
        index_name = index_config["index_name"]
        if index_name == "ta_video":
            self._add_videos(values)
        elif index_name == "ta_channel":
            self._add_channels(values)
        elif index_name == "ta_playlist":
            self._add_playlists(values)

    def _add_videos(self, values: list[str]) -> None:
        """add list of videos to reindex queue"""
        if not values:
            return

        queue_name = self.REINDEX_CONFIG["video"]["queue_name"]
        RedisQueue(queue_name).add_list(values)

    def _add_channels(self, values: list[str]) -> None:
        """add list of channels to reindex queue"""
        queue_name = self.REINDEX_CONFIG["channel"]["queue_name"]
        RedisQueue(queue_name).add_list(values)

        if self.extract_videos:
            for channel_id in values:
                all_videos = self._get_channel_videos(channel_id)
                self._add_videos(all_videos)

    def _add_playlists(self, values: list[str]) -> None:
        """add list of playlists to reindex queue"""
        queue_name = self.REINDEX_CONFIG["playlist"]["queue_name"]
        RedisQueue(queue_name).add_list(values)

        if self.extract_videos:
            for playlist_id in values:
                all_videos = self._get_playlist_videos(playlist_id)
                self._add_videos(all_videos)

    def _get_channel_videos(self, channel_id: str) -> list[str]:
        """get all videos from channel"""
        data = {
            "query": {"term": {"channel.channel_id": {"value": channel_id}}},
            "_source": ["youtube_id"],
        }
        all_results = IndexPaginate("ta_video", data).get_results()
        return [i["youtube_id"] for i in all_results]

    def _get_playlist_videos(self, playlist_id: str) -> list[str]:
        """get all videos from playlist"""
        data = {
            "query": {"term": {"playlist.keyword": {"value": playlist_id}}},
            "_source": ["youtube_id"],
        }
        all_results = IndexPaginate("ta_video", data).get_results()
        return [i["youtube_id"] for i in all_results]


class Reindex(ReindexBase):
    """reindex all documents from redis queue"""

    def __init__(self, task=False):
        super().__init__()
        self.task = task
        self.processed = {
            "videos": 0,
            "channels": 0,
            "playlists": 0,
        }

    def reindex_all(self) -> None:
        """reindex all in queue"""
        if not self.cookie_is_valid():
            print("[reindex] cookie invalid, exiting...")
            return

        for name, index_config in self.REINDEX_CONFIG.items():
            if not RedisQueue(index_config["queue_name"]).length():
                continue

            self.reindex_type(name, index_config)

    def reindex_type(self, name: str, index_config: ReindexConfigType) -> None:
        """reindex all of a single index"""
        reindex = self._get_reindex_map(index_config["index_name"])
        queue = RedisQueue(index_config["queue_name"])
        while True:
            total = queue.max_score()
            youtube_id, idx = queue.get_next()
            if not youtube_id or not idx or not total:
                break

            if self.task:
                self._notify(name, total, idx)

            reindex(youtube_id)
            sleep_interval = self.config["downloads"].get("sleep_interval", 0)
            sleep(sleep_interval)

    def _get_reindex_map(self, index_name: str) -> Callable:
        """return def to run for index"""
        def_map = {
            "ta_video": self._reindex_single_video,
            "ta_channel": self._reindex_single_channel,
            "ta_playlist": self._reindex_single_playlist,
        }

        return def_map[index_name]

    def _notify(self, name: str, total: int, idx: int) -> None:
        """send notification back to task"""
        message = [f"Reindexing {name.title()}s {idx}/{total}"]
        progress = idx / total
        self.task.send_progress(message, progress=progress)

    def _reindex_single_video(self, youtube_id: str) -> None:
        """refresh data for single video"""
        video = YoutubeVideo(youtube_id)

        # read current state
        video.get_from_es()
        if not video.json_data:
            return

        es_meta = video.json_data.copy()

        # get new
        media_url = os.path.join(
            EnvironmentSettings.MEDIA_DIR, es_meta["media_url"]
        )
        video.build_json(media_path=media_url)
        if not video.youtube_meta:
            video.deactivate()
            return

        video.delete_subtitles(subtitles=es_meta.get("subtitles"))
        video.check_subtitles()

        # add back
        video.json_data["player"] = es_meta.get("player")
        video.json_data["date_downloaded"] = es_meta.get("date_downloaded")
        video.json_data["channel"] = es_meta.get("channel")
        if es_meta.get("playlist"):
            video.json_data["playlist"] = es_meta.get("playlist")

        video.upload_to_es()

        thumb_handler = ThumbManager(youtube_id)
        thumb_handler.delete_video_thumb()
        thumb_handler.download_video_thumb(video.json_data["vid_thumb_url"])

        Comments(youtube_id, config=self.config).reindex_comments()
        self.processed["videos"] += 1

    def _reindex_single_channel(self, channel_id: str) -> None:
        """refresh channel data and sync to videos"""
        # read current state
        channel = YoutubeChannel(channel_id)
        channel.get_from_es()
        if not channel.json_data:
            return

        es_meta = channel.json_data.copy()

        # get new
        channel.get_from_youtube()
        if not channel.youtube_meta:
            channel.deactivate()
            channel.get_from_es()
            channel.sync_to_videos()
            return

        channel.process_youtube_meta()
        channel.get_channel_art()

        # add back
        channel.json_data["channel_subscribed"] = es_meta["channel_subscribed"]
        overwrites = es_meta.get("channel_overwrites")
        if overwrites:
            channel.json_data["channel_overwrites"] = overwrites

        channel.upload_to_es()
        channel.sync_to_videos()
        ChannelFullScan(channel_id).scan()
        self.processed["channels"] += 1

    def _reindex_single_playlist(self, playlist_id: str) -> None:
        """refresh playlist data"""
        playlist = YoutubePlaylist(playlist_id)
        playlist.get_from_es()
        if (
            not playlist.json_data
            or playlist.json_data["playlist_type"] == "custom"
        ):
            return

        is_active = playlist.update_playlist()
        if not is_active:
            playlist.deactivate()
            return

        self.processed["playlists"] += 1

    def cookie_is_valid(self) -> bool:
        """return true if cookie is enabled and valid"""
        if not self.config["downloads"]["cookie_import"]:
            # is not activated, continue reindex
            return True

        valid = CookieHandler(self.config).validate()
        return valid

    def build_message(self) -> str:
        """build progress message"""
        message = ""
        for key, value in self.processed.items():
            if value:
                message = message + f"{value} {key}, "

        if message:
            message = f"reindexed {message.rstrip(', ')}"

        return message


class ReindexProgress(ReindexBase):
    """
    get progress of reindex task
    request_type: key of self.REINDEX_CONFIG
    request_id: id of request_type
    return = {
        "state": "running" | "queued" | False
        "total_queued": int
        "in_queue_name": "queue_name"
    }
    """

    def __init__(self, request_type=False, request_id=False):
        super().__init__()
        self.request_type = request_type
        self.request_id = request_id

    def get_progress(self) -> dict:
        """get progress from task"""
        queue_name, request_type = self._get_queue_name()
        total = self._get_total_in_queue(queue_name)

        progress = {
            "total_queued": total,
            "type": request_type,
        }
        state = self._get_state(total, queue_name)
        progress.update(state)

        return progress

    def _get_queue_name(self):
        """return queue_name, queue_type, raise exception on error"""
        if not self.request_type:
            return "all", "all"

        reindex_config = self.REINDEX_CONFIG.get(self.request_type)
        if not reindex_config:
            print(f"reindex_config not found: {self.request_type}")
            raise ValueError

        return reindex_config["queue_name"], self.request_type

    def _get_total_in_queue(self, queue_name):
        """get all items in queue"""
        total = 0
        if queue_name == "all":
            queues = [i["queue_name"] for i in self.REINDEX_CONFIG.values()]
            for queue in queues:
                total += len(RedisQueue(queue).get_all())
        else:
            total += len(RedisQueue(queue_name).get_all())

        return total

    def _get_state(self, total, queue_name):
        """get state based on request_id"""
        state_dict = {}
        if self.request_id:
            state = RedisQueue(queue_name).in_queue(self.request_id)
            state_dict.update({"id": self.request_id, "state": state})

            return state_dict

        if total:
            state = "running"
        else:
            state = "empty"

        state_dict.update({"state": state})

        return state_dict


class ChannelFullScan:
    """
    update from v0.3.0 to v0.3.1
    full scan of channel to fix vid_type mismatch
    """

    def __init__(self, channel_id):
        self.channel_id = channel_id
        self.to_update = False

    def scan(self):
        """match local with remote"""
        print(f"{self.channel_id}: start full scan")
        all_local_videos = self._get_all_local()
        all_remote_videos = self._get_all_remote()
        self.to_update = []
        for video in all_local_videos:
            video_id = video["youtube_id"]
            remote_match = [i for i in all_remote_videos if i[0] == video_id]
            if not remote_match:
                print(f"{video_id}: no remote match found")
                continue

            expected_type = remote_match[0][-1]
            if video["vid_type"] != expected_type:
                self.to_update.append(
                    {
                        "video_id": video_id,
                        "vid_type": expected_type,
                    }
                )

        self.update()

    def _get_all_remote(self):
        """get all channel videos"""
        sub = ChannelSubscription()
        all_remote_videos = sub.get_last_youtube_videos(
            self.channel_id, limit=False
        )

        return all_remote_videos

    def _get_all_local(self):
        """get all local indexed channel_videos"""
        channel = YoutubeChannel(self.channel_id)
        all_local_videos = channel.get_channel_videos()

        return all_local_videos

    def update(self):
        """build bulk query for updates"""
        if not self.to_update:
            print(f"{self.channel_id}: nothing to update")
            return

        print(f"{self.channel_id}: fixing {len(self.to_update)} videos")
        bulk_list = []
        for video in self.to_update:
            action = {
                "update": {"_id": video.get("video_id"), "_index": "ta_video"}
            }
            source = {"doc": {"vid_type": video.get("vid_type")}}
            bulk_list.append(json.dumps(action))
            bulk_list.append(json.dumps(source))
        # add last newline
        bulk_list.append("\n")
        data = "\n".join(bulk_list)
        _, _ = ElasticWrap("_bulk").post(data=data, ndjson=True)
