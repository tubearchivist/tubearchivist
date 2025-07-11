"""
Functionality:
- handle channel subscriptions
- handle playlist subscriptions
"""

from appsettings.src.config import AppConfig
from channel.src.index import YoutubeChannel
from channel.src.remote_query import VideoQueryBuilder
from common.src.helper import get_channels, get_playlists
from common.src.urlparser import ParsedURLType, Parser
from download.src.queue import PendingList
from playlist.src.index import YoutubePlaylist
from video.src.constants import VideoTypeEnum
from video.src.index import YoutubeVideo


class ChannelSubscription:
    """scan subscribed channels to find missing videos to add to pending"""

    def __init__(self, task=None):
        self.config = AppConfig().config
        self.task = task

    def find_missing(self) -> int:
        """find missing videos from channel subscriptions"""
        all_channels = get_channels(
            subscribed_only=True, source=["channel_id", "channel_overwrites"]
        )
        if not all_channels:
            return 0

        all_channel_urls: list[ParsedURLType] = []

        for channel in all_channels:
            queries = VideoQueryBuilder(
                config=self.config,
                channel_overwrites=channel.get("channel_overwrites", {}),
            ).build_queries(video_type=None)

            for query in queries:
                all_channel_urls.append(
                    ParsedURLType(
                        type="channel",
                        url=channel["channel_id"],
                        vid_type=query[0],
                        limit=query[1],
                    )
                )

        pending_handler = PendingList(
            youtube_ids=all_channel_urls,
            task=self.task,
            auto_start=self.config["subscriptions"].get("auto_start", False),
            flat=self.config["subscriptions"].get("extract_flat", False),
        )
        pending_handler.parse_url_list()
        added = pending_handler.add_to_pending()

        return added


class PlaylistSubscription:
    """scan subscribed playlists for videos to add to pending"""

    def __init__(self, task=None):
        self.config = AppConfig().config
        self.task = task

    def find_missing(self) -> int:
        """find missing"""
        all_playlists = get_playlists(
            subscribed_only=True, source=["playlist_id"]
        )
        if not all_playlists:
            return 0

        size_limit = self.config["subscriptions"]["channel_size"]
        all_playlist_urls: list[ParsedURLType] = []
        for playlist in all_playlists:
            all_playlist_urls.append(
                ParsedURLType(
                    type="playlist",
                    url=playlist["playlist_id"],
                    vid_type=VideoTypeEnum.UNKNOWN,
                    limit=size_limit,
                )
            )

        pending_handler = PendingList(
            youtube_ids=all_playlist_urls,
            task=self.task,
            auto_start=self.config["subscriptions"].get("auto_start", False),
            flat=self.config["subscriptions"].get("extract_flat", False),
        )
        pending_handler.parse_url_list()
        added = pending_handler.add_to_pending()

        return added


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

        added = 0
        added += ChannelSubscription(task=self.task).find_missing()
        if self.task and not self.task.is_stopped():
            added += PlaylistSubscription(task=self.task).find_missing()

        return added


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

            playlist = YoutubePlaylist(item["url"])
            playlist.change_subscribe(new_subscribe_state=True)
            return

        if item["type"] == "video":
            # extract channel id from video
            video = YoutubeVideo(item["url"])
            video.get_from_youtube()
            video.process_youtube_meta()
            channel_id = video.channel_id
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
        YoutubeChannel(channel_id).change_subscribe(new_subscribe_state=True)

    def _notify(self, idx, item, total):
        """send notification message to redis"""
        subscribe_type = item["type"].title()
        message_lines = [
            f"Subscribe to {subscribe_type}",
            f"Progress: {idx + 1}/{total}",
        ]
        self.task.send_progress(message_lines, progress=(idx + 1) / total)
