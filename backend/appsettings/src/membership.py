"""
interact with members.tubearchivist.com
code related to sponsor perks
"""

from os import environ

import requests
from appsettings.src.config import AppConfig
from common.src.helper import get_channels
from common.src.ta_redis import RedisArchivist


class Membership:
    """membership"""

    BASE_URL = environ.get("MB_URL", "https://members.tubearchivist.com")
    REDIS_KEY = "MB:KEY"

    def __init__(self):
        self.config = AppConfig().config

    def get_profile(self):
        """get profile"""
        response = requests.get(
            f"{self.BASE_URL}/api/profile/me/",
            headers=self._get_headers(),
            timeout=30,
        )
        return response

    def _get_headers(self):
        """get headers with api key"""
        token = RedisArchivist().get_message_dict(self.REDIS_KEY)
        if not token:
            raise ValueError("expected MB_API_KEY")

        token_str = token["token"]

        return {"Authorization": f"Token {token_str}"}

    def sync_subs(self):
        """sync subscriptions, works if within max limits"""
        to_sync = self._get_to_sync()
        response = requests.post(
            f"{self.BASE_URL}/api/profile/subscription/?delete=true",
            headers=self._get_headers(),
            json=to_sync,
            timeout=30,
        )
        return response

    def _get_to_sync(self):
        """get channels to sync"""
        to_sync = []
        subscribed = get_channels(subscribed_only=True)
        for channel in subscribed:
            overwrites = channel.get("channel_overwrites", {})
            to_sync.append(
                {
                    "channel_id": channel["channel_id"],
                    "notify_videos": self._notify_videos(overwrites),
                    "notify_streams": self._notify_streams(overwrites),
                    "notify_shorts": self._notify_shorts(overwrites),
                }
            )

        return to_sync

    def _notify_videos(self, overwrites: dict) -> bool:
        """notify videos"""
        if overwrites.get("subscriptions_channel_size") == 0:
            return False

        return self.config["subscriptions"].get("channel_size") != 0

    def _notify_streams(self, overwrites: dict) -> bool:
        """notify streams"""
        if overwrites.get("subscriptions_live_channel_size") == 0:
            return False

        return self.config["subscriptions"].get("live_channel_size") != 0

    def _notify_shorts(self, overwrites: dict) -> bool:
        """notify shorts"""
        if overwrites.get("subscriptions_shorts_channel_size") == 0:
            return False

        return self.config["subscriptions"].get("shorts_channel_size") != 0
