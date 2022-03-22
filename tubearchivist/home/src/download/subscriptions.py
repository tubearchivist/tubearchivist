"""
Functionality:
- handle channel subscriptions
- handle playlist subscriptions
"""

import yt_dlp
from home.src.download import queue  # partial import
from home.src.es.connect import IndexPaginate
from home.src.index.channel import YoutubeChannel
from home.src.index.playlist import YoutubePlaylist
from home.src.ta.config import AppConfig
from home.src.ta.ta_redis import RedisArchivist


class ChannelSubscription:
    """manage the list of channels subscribed"""

    def __init__(self):
        config = AppConfig().config
        self.es_url = config["application"]["es_url"]
        self.es_auth = config["application"]["es_auth"]
        self.channel_size = config["subscriptions"]["channel_size"]

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

    def get_last_youtube_videos(self, channel_id, limit=True):
        """get a list of last videos from channel"""
        url = f"https://www.youtube.com/channel/{channel_id}/videos"
        obs = {
            "default_search": "ytsearch",
            "quiet": True,
            "skip_download": True,
            "extract_flat": True,
        }
        if limit:
            obs["playlistend"] = self.channel_size

        try:
            chan = yt_dlp.YoutubeDL(obs).extract_info(url, download=False)
        except yt_dlp.utils.DownloadError:
            print(f"{channel_id}: failed to extract videos, skipping.")
            return False

        last_videos = [(i["id"], i["title"]) for i in chan["entries"]]
        return last_videos

    def find_missing(self):
        """add missing videos from subscribed channels to pending"""
        all_channels = self.get_channels()
        pending = queue.PendingList()
        pending.get_download()
        pending.get_indexed()

        missing_videos = []

        for idx, channel in enumerate(all_channels):
            channel_id = channel["channel_id"]
            last_videos = self.get_last_youtube_videos(channel_id)

            if last_videos:
                for video in last_videos:
                    if video[0] not in pending.to_skip:
                        missing_videos.append(video[0])
            # notify
            message = {
                "status": "message:rescan",
                "level": "info",
                "title": "Scanning channels: Looking for new videos.",
                "message": f"Progress: {idx + 1}/{len(all_channels)}",
            }
            if idx + 1 == len(all_channels):
                RedisArchivist().set_message(
                    "message:rescan", message=message, expire=4
                )
            else:
                RedisArchivist().set_message("message:rescan", message=message)

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

    def __init__(self):
        self.config = AppConfig().config

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
        data = {
            "query": {"match_all": {}},
            "sort": [{"published": {"order": "desc"}}],
        }
        all_indexed = IndexPaginate("ta_video", data).get_results()
        all_youtube_ids = [i["youtube_id"] for i in all_indexed]

        new_thumbs = []
        for idx, playlist in enumerate(new_playlists):
            url_type = playlist["type"]
            playlist_id = playlist["url"]
            if not url_type == "playlist":
                print(f"{playlist_id} not a playlist, skipping...")
                continue

            playlist_h = YoutubePlaylist(playlist_id)
            playlist_h.all_youtube_ids = all_youtube_ids
            playlist_h.build_json()
            playlist_h.json_data["playlist_subscribed"] = subscribed
            playlist_h.upload_to_es()
            playlist_h.add_vids_to_playlist()
            self.channel_validate(playlist_h.json_data["playlist_channel_id"])
            thumb = playlist_h.json_data["playlist_thumbnail"]
            new_thumbs.append((playlist_id, thumb))
            # notify
            message = {
                "status": "message:subplaylist",
                "level": "info",
                "title": "Subscribing to Playlists",
                "message": f"Processing {idx + 1} of {len(new_playlists)}",
            }
            RedisArchivist().set_message(
                "message:subplaylist", message=message
            )

        return new_thumbs

    @staticmethod
    def channel_validate(channel_id):
        """make sure channel of playlist is there"""
        channel = YoutubeChannel(channel_id)
        channel.build_json()

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
        to_ignore = self.get_to_ignore()

        missing_videos = []
        for idx, playlist_id in enumerate(all_playlists):
            size_limit = self.config["subscriptions"]["channel_size"]
            playlist = YoutubePlaylist(playlist_id)
            playlist.update_playlist()
            if not playlist:
                playlist.deactivate()
                continue

            playlist_entries = playlist.json_data["playlist_entries"]
            if size_limit:
                del playlist_entries[size_limit:]

            all_missing = [i for i in playlist_entries if not i["downloaded"]]

            message = {
                "status": "message:rescan",
                "level": "info",
                "title": "Scanning playlists: Looking for new videos.",
                "message": f"Progress: {idx + 1}/{len(all_playlists)}",
            }
            RedisArchivist().set_message("message:rescan", message=message)

            for video in all_missing:
                youtube_id = video["youtube_id"]
                if youtube_id not in to_ignore:
                    missing_videos.append(youtube_id)

        return missing_videos
