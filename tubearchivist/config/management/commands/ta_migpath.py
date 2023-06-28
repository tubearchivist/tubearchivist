"""filepath migration from v0.3.6 to v0.3.7"""

import json
import os

from django.core.management.base import BaseCommand
from home.src.es.connect import ElasticWrap, IndexPaginate
from home.src.ta.config import AppConfig
from home.src.ta.helper import ignore_filelist

TOPIC = """

########################
# Filesystem Migration #
########################

"""


class Command(BaseCommand):
    """command framework"""

    # pylint: disable=no-member

    def handle(self, *args, **options):
        """run commands"""
        self.stdout.write(TOPIC)
        need_migration = self.channels_need_migration()
        if not need_migration:
            self.stdout.write(
                self.style.SUCCESS("    no channel migration needed")
            )
            return

        self.stdout.write(
            self.style.SUCCESS(f"    migrating {len(need_migration)} channels")
        )
        for channel in need_migration:
            channel_name = channel["channel_name"]
            channel_id = channel["channel_id"]
            self.stdout.write(
                self.style.SUCCESS(
                    f"    migrating {channel_name} [{channel_id}]"
                )
            )
            ChannelMigration(channel).migrate()

        self.stdout.write(
            self.style.SUCCESS("    ✓ channel migration completed")
        )

    def channels_need_migration(self):
        """get channels that need migration"""
        all_indexed = self._get_channel_indexed()
        all_folders = self._get_channel_folders()
        need_migration = []
        for channel in all_indexed:
            if channel["channel_id"] not in all_folders:
                need_migration.append(channel)

        return need_migration

    def _get_channel_indexed(self):
        """get all channels indexed"""
        all_results = IndexPaginate("ta_channel", False).get_results()

        return all_results

    def _get_channel_folders(self):
        """get all channel folders"""
        base_folder = AppConfig().config["application"]["videos"]
        existing_folders = ignore_filelist(os.listdir(base_folder))

        return existing_folders


class ChannelMigration:
    """migrate single channel"""

    def __init__(self, channel):
        self.channel = channel
        self.config = AppConfig().config
        self.videos = self.config["application"]["videos"]
        self.bulk_list = []

    def migrate(self):
        """run migration"""
        self._create_new_folder()
        all_videos = self.get_channel_videos()
        self.migrate_videos(all_videos)
        self.send_bulk()
        self.delete_old(all_videos)

    def _create_new_folder(self):
        """create new channel id folder"""
        host_uid = self.config["application"]["HOST_UID"]
        host_gid = self.config["application"]["HOST_GID"]
        new_path = os.path.join(self.videos, self.channel["channel_id"])
        if not os.path.exists(new_path):
            os.mkdir(new_path)
            if host_uid and host_gid:
                os.chown(new_path, host_uid, host_gid)

    def get_channel_videos(self):
        """get all videos of channel"""
        data = {
            "query": {
                "term": {
                    "channel.channel_id": {"value": self.channel["channel_id"]}
                }
            }
        }
        all_videos = IndexPaginate("ta_video", data).get_results()

        return all_videos

    def migrate_videos(self, all_videos):
        """migrate all videos of channel"""
        for video in all_videos:
            new_media_url = self._move_video_file(video)
            all_subtitles = self._move_subtitles(video)
            action = {
                "update": {"_id": video["youtube_id"], "_index": "ta_video"}
            }
            source = {"doc": {"media_url": new_media_url}}
            if all_subtitles:
                source["doc"].update({"subtitles": all_subtitles})

            self.bulk_list.append(json.dumps(action))
            self.bulk_list.append(json.dumps(source))

    def _move_video_file(self, video):
        """move video file to new location"""
        old_path = os.path.join(self.videos, video["media_url"])
        if not os.path.exists(old_path):
            print(f"did not find expected video at {old_path}")
            return False

        new_media_url = os.path.join(
            self.channel["channel_id"], video["youtube_id"] + ".mp4"
        )
        os.rename(old_path, os.path.join(self.videos, new_media_url))

        return new_media_url

    def _move_subtitles(self, video):
        """move subtitle files to new location"""
        all_subtitles = video.get("subtitles")
        if not all_subtitles:
            return False

        for subtitle in all_subtitles:
            old_path = os.path.join(self.videos, subtitle["media_url"])
            if not os.path.exists(old_path):
                print(f"did not find expected subtitle at {old_path}")
                continue

            ext = ".".join(old_path.split(".")[-2:])
            new_media_url = os.path.join(
                self.channel["channel_id"], video["youtube_id"] + f".{ext}"
            )
            os.rename(old_path, os.path.join(self.videos, new_media_url))
            subtitle["media_url"] = new_media_url

        return all_subtitles

    def send_bulk(self):
        """send bulk request to update index with new urls"""
        if not self.bulk_list:
            print("nothing to update")
            return

        self.bulk_list.append("\n")
        data = "\n".join(self.bulk_list)
        response, status = ElasticWrap("_bulk").post(data=data, ndjson=True)
        if not status == 200:
            print(response)

    def delete_old(self, all_videos):
        """delete old folder path if empty"""
        if not all_videos:
            return

        channel_name = os.path.split(all_videos[0]["media_url"])[0]
        old_path = os.path.join(self.videos, channel_name)
        if os.path.exists(old_path) and not os.listdir(old_path):
            os.rmdir(old_path)
            return

        print(f"failed to clean up old folder {old_path}")
