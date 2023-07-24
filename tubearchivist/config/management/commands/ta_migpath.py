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

        handler = FolderMigration()
        to_migrate = handler.get_to_migrate()
        if not to_migrate:
            self.stdout.write(
                self.style.SUCCESS("    no channel migration needed\n")
            )
            return

        self.stdout.write(self.style.SUCCESS("    migrating channels"))
        total_channels = handler.create_folders(to_migrate)
        self.stdout.write(
            self.style.SUCCESS(f"    created {total_channels} channels")
        )

        self.stdout.write(
            self.style.SUCCESS(f"    migrating {len(to_migrate)} videos")
        )
        handler.migrate_videos(to_migrate)
        self.stdout.write(self.style.SUCCESS("    update videos in index"))
        handler.send_bulk()

        self.stdout.write(self.style.SUCCESS("    cleanup old folders"))
        handler.delete_old()

        self.stdout.write(self.style.SUCCESS("    ✓ migration completed\n"))


class FolderMigration:
    """migrate video archive folder"""

    def __init__(self):
        self.config = AppConfig().config
        self.videos = self.config["application"]["videos"]
        self.bulk_list = []

    def get_to_migrate(self):
        """get videos to migrate"""
        script = (
            "doc['media_url'].value == "
            + "doc['channel.channel_id'].value + '/'"
            + " + doc['youtube_id'].value + '.mp4'"
        )
        data = {
            "query": {"bool": {"must_not": [{"script": {"script": script}}]}},
            "_source": [
                "youtube_id",
                "media_url",
                "channel.channel_id",
                "subtitles",
            ],
        }
        response = IndexPaginate("ta_video", data).get_results()

        return response

    def create_folders(self, to_migrate):
        """create required channel folders"""
        host_uid = self.config["application"]["HOST_UID"]
        host_gid = self.config["application"]["HOST_GID"]
        all_channel_ids = {i["channel"]["channel_id"] for i in to_migrate}

        for channel_id in all_channel_ids:
            new_folder = os.path.join(self.videos, channel_id)
            os.makedirs(new_folder, exist_ok=True)
            if host_uid and host_gid:
                os.chown(new_folder, host_uid, host_gid)

        return len(all_channel_ids)

    def migrate_videos(self, to_migrate):
        """migrate all videos of channel"""
        for video in to_migrate:
            new_media_url = self._move_video_file(video)
            if not new_media_url:
                continue

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
            video["channel"]["channel_id"], video["youtube_id"] + ".mp4"
        )
        new_path = os.path.join(self.videos, new_media_url)
        os.rename(old_path, new_path)

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

            new_media_url = os.path.join(
                video["channel"]["channel_id"],
                f"{video.get('youtube_id')}.{subtitle.get('lang')}.vtt",
            )
            new_path = os.path.join(self.videos, new_media_url)
            os.rename(old_path, new_path)
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

    def delete_old(self):
        """delete old empty folders"""
        all_folders = ignore_filelist(os.listdir(self.videos))
        for folder in all_folders:
            folder_path = os.path.join(self.videos, folder)
            if not ignore_filelist(os.listdir(folder_path)):
                os.rmdir(folder_path)
