"""
migration for 0.5.4 to 0.5.5
index channel_tabs for subscribed channels
"""

import time

from channel.src.index import YoutubeChannel
from common.src.helper import get_channels
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """command"""

    def handle(self, *args, **kwargs):
        """handle task"""

        self.stdout.write("channel tags initial index")

        channels = get_channels(subscribed_only=True, source=["channel_id"])

        for es_channel in channels:
            channel = YoutubeChannel(es_channel["channel_id"])
            channel.get_from_es()
            channel_name = channel.json_data["channel_name"]
            channel_tabs = channel.get_channel_tabs()
            channel.json_data["channel_tabs"] = channel_tabs
            channel.upload_to_es()
            channel.sync_to_videos()
            self.stdout.write(
                self.style.SUCCESS(
                    f"    ✓ updated '{channel_name}' tabs: {channel_tabs}"
                )
            )
            time.sleep(5)
