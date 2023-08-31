"""
Functionality:
- handle channel subscriptions
- handle playlist subscriptions
"""

from home.src.download import queue  # partial import
from home.src.download.thumbnails import ThumbManager
from home.src.download.yt_dlp_base import YtWrap
from home.src.es.connect import IndexPaginate
from home.src.index.channel import YoutubeChannel
from home.src.index.playlist import YoutubePlaylist
from home.src.index.video_constants import VideoTypeEnum
from home.src.ta.config import AppConfig
from home.src.ta.urlparser import Parser


class ChannelSubscription:
    """manage the list of channels subscribed"""

    def __init__(self, task=False):
        self.config = AppConfig().config
        self.task = task

    @staticmethod
    def get_channels(subscribed_only=True):
        """get a list of all channels subscribed to"""
        data = {
            "sort": [{"channel_name.keyword": {"order": "asc"}}],
        }
        if subscribed_only:
            data["query"] = {"term": {"channel_subscribed": {"value": True}}}
        else:
            data["query"] = {"match_all": {}}

        all_channels = IndexPaginate("ta_channel", data).get_results()

        return all_channels

    def get_last_youtube_videos(
        self, channel_id, limit=True, query_filter=VideoTypeEnum.UNKNOWN
    ):
        """get a list of last videos from channel"""
        queries = self._build_queries(query_filter, limit)

        last_videos = []

        for vid_type_enum, limit_amount in queries:
            obs = {
                "skip_download": True,
                "extract_flat": True,
            }
            if limit:
                obs["playlistend"] = limit_amount

            vid_type = vid_type_enum.value
            channel = YtWrap(obs, self.config).extract(
                f"https://www.youtube.com/channel/{channel_id}/{vid_type}"
            )
            if not channel:
                continue
            last_videos.extend(
                [(i["id"], i["title"], vid_type) for i in channel["entries"]]
            )

        return last_videos

    def _build_queries(self, query_filter, limit):
        """build query list for vid_type"""
        limit_map = {
            "videos": self.config["subscriptions"]["channel_size"],
            "streams": self.config["subscriptions"]["live_channel_size"],
            "shorts": self.config["subscriptions"]["shorts_channel_size"],
        }

        queries = []

        if query_filter and query_filter.value != "unknown":
            if limit:
                query_limit = limit_map.get(query_filter.value)
            else:
                query_limit = False

            queries.append((query_filter, query_limit))

            return queries

        for query_item, default_limit in limit_map.items():
            if not default_limit:
                # is deactivated in config
                continue

            if limit:
                query_limit = default_limit
            else:
                query_limit = False

            queries.append((VideoTypeEnum(query_item), query_limit))

        return queries

    def find_missing(self):
        """add missing videos from subscribed channels to pending"""
        all_channels = self.get_channels()
        if not all_channels:
            return False

        pending = queue.PendingList()
        pending.get_download()
        pending.get_indexed()

        missing_videos = []

        total = len(all_channels)
        for idx, channel in enumerate(all_channels):
            channel_id = channel["channel_id"]
            print(f"{channel_id}: find missing videos.")
            last_videos = self.get_last_youtube_videos(channel_id)

            if last_videos:
                for video_id, _, vid_type in last_videos:
                    if video_id not in pending.to_skip:
                        missing_videos.append((video_id, vid_type))

            if not self.task:
                continue

            if self.task:
                if self.task.is_stopped():
                    self.task.send_progress(["Received Stop signal."])
                    break

                self.task.send_progress(
                    message_lines=[f"Scanning Channel {idx + 1}/{total}"],
                    progress=(idx + 1) / total,
                )

        return missing_videos

    @staticmethod
    def change_subscribe(channel_id, channel_subscribed):
        """subscribe or unsubscribe from channel and update"""
        channel = YoutubeChannel(channel_id)
        channel.build_json()
        channel.json_data["channel_subscribed"] = channel_subscribed
        channel.upload_to_es()
        channel.sync_to_videos()


class PlaylistSubscription:
    """manage the playlist download functionality"""

    def __init__(self, task=False):
        self.config = AppConfig().config
        self.task = task

    @staticmethod
    def get_playlists(subscribed_only=True):
        """get a list of all active playlists"""
        data = {
            "sort": [{"playlist_channel.keyword": {"order": "desc"}}],
        }
        data["query"] = {
            "bool": {"must": [{"term": {"playlist_active": {"value": True}}}]}
        }
        if subscribed_only:
            data["query"]["bool"]["must"].append(
                {"term": {"playlist_subscribed": {"value": True}}}
            )

        all_playlists = IndexPaginate("ta_playlist", data).get_results()

        return all_playlists

    def process_url_str(self, new_playlists, subscribed=True):
        """process playlist subscribe form url_str"""
        data = {"query": {"match_all": {}}, "_source": ["youtube_id"]}
        all_indexed = IndexPaginate("ta_video", data).get_results()
        all_youtube_ids = [i["youtube_id"] for i in all_indexed]

        for idx, playlist in enumerate(new_playlists):
            playlist_id = playlist["url"]
            if not playlist["type"] == "playlist":
                print(f"{playlist_id} not a playlist, skipping...")
                continue

            playlist_h = YoutubePlaylist(playlist_id)
            playlist_h.all_youtube_ids = all_youtube_ids
            playlist_h.build_json()
            playlist_h.json_data["playlist_subscribed"] = subscribed
            playlist_h.upload_to_es()
            playlist_h.add_vids_to_playlist()
            self.channel_validate(playlist_h.json_data["playlist_channel_id"])

            url = playlist_h.json_data["playlist_thumbnail"]
            thumb = ThumbManager(playlist_id, item_type="playlist")
            thumb.download_playlist_thumb(url)

            if self.task:
                self.task.send_progress(
                    message_lines=[
                        f"Processing {idx + 1} of {len(new_playlists)}"
                    ],
                    progress=(idx + 1) / len(new_playlists),
                )

    @staticmethod
    def channel_validate(channel_id):
        """make sure channel of playlist is there"""
        channel = YoutubeChannel(channel_id)
        channel.build_json(upload=True)

    @staticmethod
    def change_subscribe(playlist_id, subscribe_status):
        """change the subscribe status of a playlist"""
        playlist = YoutubePlaylist(playlist_id)
        playlist.build_json()
        playlist.json_data["playlist_subscribed"] = subscribe_status
        playlist.upload_to_es()

    @staticmethod
    def get_to_ignore():
        """get all youtube_ids already downloaded or ignored"""
        pending = queue.PendingList()
        pending.get_download()
        pending.get_indexed()

        return pending.to_skip

    def find_missing(self):
        """find videos in subscribed playlists not downloaded yet"""
        all_playlists = [i["playlist_id"] for i in self.get_playlists()]
        if not all_playlists:
            return False

        to_ignore = self.get_to_ignore()

        missing_videos = []
        total = len(all_playlists)
        for idx, playlist_id in enumerate(all_playlists):
            size_limit = self.config["subscriptions"]["channel_size"]
            playlist = YoutubePlaylist(playlist_id)
            is_active = playlist.update_playlist()
            if not is_active:
                playlist.deactivate()
                continue

            playlist_entries = playlist.json_data["playlist_entries"]
            if size_limit:
                del playlist_entries[size_limit:]

            all_missing = [i for i in playlist_entries if not i["downloaded"]]

            for video in all_missing:
                youtube_id = video["youtube_id"]
                if youtube_id not in to_ignore:
                    missing_videos.append(youtube_id)

            if not self.task:
                continue

            if self.task:
                self.task.send_progress(
                    message_lines=[f"Scanning Playlists {idx + 1}/{total}"],
                    progress=(idx + 1) / total,
                )
                if self.task.is_stopped():
                    self.task.send_progress(["Received Stop signal."])
                    break

        return missing_videos


class SubscriptionScanner:
    """add missing videos to queue"""

    def __init__(self, task=False):
        self.task = task
        self.missing_videos = False
        self.auto_start = AppConfig().config["subscriptions"].get("auto_start")

    def scan(self):
        """scan channels and playlists"""
        if self.task:
            self.task.send_progress(["Rescanning channels and playlists."])

        self.missing_videos = []
        self.scan_channels()
        if self.task and not self.task.is_stopped():
            self.scan_playlists()

        return self.missing_videos

    def scan_channels(self):
        """get missing from channels"""
        channel_handler = ChannelSubscription(task=self.task)
        missing = channel_handler.find_missing()
        if not missing:
            return

        for vid_id, vid_type in missing:
            self.missing_videos.append(
                {"type": "video", "vid_type": vid_type, "url": vid_id}
            )

    def scan_playlists(self):
        """get missing from playlists"""
        playlist_handler = PlaylistSubscription(task=self.task)
        missing = playlist_handler.find_missing()
        if not missing:
            return

        for i in missing:
            self.missing_videos.append(
                {
                    "type": "video",
                    "vid_type": VideoTypeEnum.VIDEOS.value,
                    "url": i,
                }
            )


class SubscriptionHandler:
    """subscribe to channels and playlists from url_str"""

    def __init__(self, url_str, task=False):
        self.url_str = url_str
        self.task = task
        self.to_subscribe = False

    def subscribe(self, expected_type=False):
        """subscribe to url_str items"""
        if self.task:
            self.task.send_progress(["Processing form content."])
        self.to_subscribe = Parser(self.url_str).parse()

        total = len(self.to_subscribe)
        for idx, item in enumerate(self.to_subscribe):
            if self.task:
                self._notify(idx, item, total)

            self.subscribe_type(item, expected_type=expected_type)

    def subscribe_type(self, item, expected_type):
        """process single item"""
        if item["type"] == "playlist":
            if expected_type and expected_type != "playlist":
                raise TypeError(
                    f"expected {expected_type} url but got {item.get('type')}"
                )

            PlaylistSubscription().process_url_str([item])
            return

        if item["type"] == "video":
            # extract channel id from video
            vid = queue.PendingList().get_youtube_details(item["url"])
            channel_id = vid["channel_id"]
        elif item["type"] == "channel":
            channel_id = item["url"]
        else:
            raise ValueError("failed to subscribe to: " + item["url"])

        if expected_type and expected_type != "channel":
            raise TypeError(
                f"expected {expected_type} url but got {item.get('type')}"
            )

        self._subscribe(channel_id)

    def _subscribe(self, channel_id):
        """subscribe to channel"""
        ChannelSubscription().change_subscribe(
            channel_id, channel_subscribed=True
        )

    def _notify(self, idx, item, total):
        """send notification message to redis"""
        subscribe_type = item["type"].title()
        message_lines = [
            f"Subscribe to {subscribe_type}",
            f"Progress: {idx + 1}/{total}",
        ]
        self.task.send_progress(message_lines, progress=(idx + 1) / total)
