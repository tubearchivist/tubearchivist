"""bulk metadata embedding"""

import json
import os
import shutil

from appsettings.src.config import AppConfig, AppConfigType
from channel.serializers import ChannelSerializer
from channel.src.index import YoutubeChannel
from common.src.env_settings import EnvironmentSettings
from common.src.es_connect import ElasticWrap, IndexPaginate
from mutagen.mp4 import MP4, MP4FreeForm
from video.serializers import (
    CommentsSerializer,
    SubtitleFragmentSerializer,
    VideoSerializer,
)
from video.src.comments import Comments
from video.src.index import YoutubeVideo
from video.src.subtitle import SubtitleParser, YoutubeSubtitle


class MetadataEmbed:
    """sync metadata to videos in bulk"""

    INDEX_NAME = "ta_video"

    def __init__(self, task=False):
        self.task = task

    def embed(self):
        """entry point"""
        data = {
            "query": {"match_all": {}},
            "_source": ["youtube_id"],
        }
        paginate = IndexPaginate(
            index_name=self.INDEX_NAME,
            data=data,
            size=200,
            callback=MetadataEmbedCallback,
            task=self.task,
            total=self._get_total(),
        )
        _ = paginate.get_results()

    def _get_total(self):
        """get total documents in index"""
        path = f"{self.INDEX_NAME}/_count"
        response, _ = ElasticWrap(path).get()

        return response.get("count")


class MetadataEmbedCallback:
    """callback for metadata embed"""

    def __init__(self, source, index_name, counter=0):
        self.source = source
        self.index_name = index_name
        self.counter = counter

    def run(self):
        """run embed"""
        for video in self.source:
            youtube_id = video["_source"]["youtube_id"]
            YoutubeVideo(youtube_id).embed_metadata()


class IndexFromEmbed:
    """restore from embedded metadata, potential untrusted"""

    VIDEOS_BASE = EnvironmentSettings.MEDIA_DIR
    HOST_UID = EnvironmentSettings.HOST_UID
    HOST_GID = EnvironmentSettings.HOST_GID

    def __init__(
        self,
        file_path: str,
        reset_user_conf: bool = True,
        config: AppConfigType | None = None,
    ):
        self.file_path = file_path
        self.reset_user_conf = reset_user_conf
        self.config = config

    def run_index(self) -> None:
        """run index"""
        if not self.config:
            self.config = AppConfig().config

        json_embed = self._get_embedded()
        if not json_embed:
            return

        channel_data_clean = self.index_channel(json_embed)
        video = self.index_video(json_embed, channel_data_clean)
        self.archive_video(video)
        self.index_subtitles(json_embed, video)
        self.index_comments(json_embed)

    def _get_embedded(self) -> dict | None:
        """get embedded metadata"""
        video = MP4(self.file_path)
        ta_data = video.get("----:com.tubearchivist:ta")
        if not ta_data:
            return None

        if not isinstance(ta_data, list):
            raise ValueError(f"[{self.file_path}] unexpected embedded data")

        to_decode = ta_data[0]

        if not isinstance(to_decode, MP4FreeForm):
            raise ValueError(f"[{self.file_path}] unexpected embedded data")

        try:
            json_embed = json.loads(to_decode.decode())
        except Exception as exc:  # pylint: disable=broad-exception-caught
            err = f"[{self.file_path}] embedded decoding failed: {str(exc)}"
            raise ValueError(err) from exc

        if not json_embed.get("video"):
            err = f"[{self.file_path}] embedded does not contain video key"
            raise ValueError(err)

        return json_embed

    def index_channel(self, json_embed):
        """index channel"""
        channel_data = json_embed["video"].get("channel")
        if not channel_data:
            raise ValueError(f"[{self.file_path}] missing channel metadata")

        serializer = ChannelSerializer(data=channel_data)
        is_valid = serializer.is_valid()
        if not is_valid:
            err = serializer.errors
            raise ValueError(
                f"[{self.file_path}] channel serializer failed: {err}"
            )

        channel_data_clean = dict(serializer.data)
        if self.reset_user_conf:
            if "channel_overwrites" in channel_data_clean:
                channel_data_clean.pop("channel_overwrites")

            channel_data_clean["channel_subscribed"] = False

        channel = YoutubeChannel(youtube_id=channel_data_clean["channel_id"])
        channel.build_json(upload=True)
        if channel.json_data:
            return

        channel.json_data = channel_data_clean
        channel.upload_to_es()

        return channel_data_clean

    def index_video(self, json_embed, channel_data_clean):
        """index video"""
        video_data = json_embed["video"]
        video_data.pop("channel")

        serializer = VideoSerializer(data=video_data)
        is_valid = serializer.is_valid()
        if not is_valid:
            err = serializer.errors
            raise ValueError(
                f"[{self.file_path}] video serializer failed: {err}"
            )

        video_data_clean = dict(serializer.data)
        if self.reset_user_conf:
            video_data_clean["player"]["watched"] = False

        video = YoutubeVideo(youtube_id=video_data_clean["youtube_id"])
        video.build_json()
        if video.json_data:
            video.upload_to_es()
            return

        video_data_clean["channel"] = channel_data_clean
        video.json_data = video_data_clean
        video.upload_to_es()

        return video

    def archive_video(self, video):
        """archive video file"""
        channel_id = video.json_data["channel"]["channel_id"]
        folder = os.path.join(self.VIDEOS_BASE, channel_id)
        if not os.path.exists(folder):
            os.makedirs(folder)
            if self.HOST_UID and self.HOST_GID:
                os.chown(folder, self.HOST_UID, self.HOST_GID)

        new_path = os.path.join(folder, f"{video.youtube_id}.mp4")
        if self.file_path == new_path:
            # already archived
            return

        shutil.move(self.file_path, new_path, copy_function=shutil.copyfile)
        if self.HOST_UID and self.HOST_GID:
            os.chown(new_path, self.HOST_UID, self.HOST_GID)

    def index_subtitles(self, json_embed, video):
        """index subtitles"""
        subtitle_data = json_embed.get("subtitles")
        if not subtitle_data:
            return

        serializer = SubtitleFragmentSerializer(data=subtitle_data, many=True)
        is_valid = serializer.is_valid()
        if not is_valid:
            err = serializer.errors
            raise ValueError(
                f"[{self.file_path}] subtitle serializer failed: {err}"
            )

        self._process_embedded(video, subtitle_data=serializer.data)

    def _process_embedded(self, video, subtitle_data):
        """process single embedded subtitle"""
        embedded_subs = {
            (i["subtitle_lang"], i["subtitle_source"]) for i in subtitle_data
        }
        subs = YoutubeSubtitle(video)

        if video.youtube_meta:
            relevant_subtitles = subs.get_subtitles()
            indexed = subs.download_subtitles(relevant_subtitles)
        else:
            indexed = []

        for embedded_lang, embedded_source in embedded_subs:
            for sub_indexed in indexed:
                if (
                    sub_indexed.get("lang") == embedded_lang
                    and sub_indexed.get("source") == embedded_source
                ):
                    # indexed from remote
                    continue

            segments = [
                i
                for i in subtitle_data
                if i["subtitle_lang"] == embedded_lang
                and i["subtitle_source"] == embedded_source
            ]
            to_index = sorted(segments, key=lambda d: d["subtitle_index"])
            parser = SubtitleParser(
                subtitle_str="{}", lang=embedded_lang, source=embedded_source
            )

            for segment in to_index:
                parser.all_cues.append(
                    {
                        "start": segment["subtitle_start"],
                        "end": segment["subtitle_end"],
                        "text": segment["subtitle_line"],
                        "idx": segment["subtitle_index"],
                    }
                )

            subtitle_str = parser.get_subtitle_str()
            query_str = parser.create_bulk_import(to_index)
            subs.index_subtitle(query_str)

            media_url = subs.get_media_url(lang=embedded_lang)
            dest_path = os.path.join(self.VIDEOS_BASE, media_url)
            subs.write_subtitle_file(dest_path, subtitle_str)

    def index_comments(self, json_embed):
        """index comments"""
        comment_data = json_embed.get("comments")
        if not comment_data:
            return

        serializer = CommentsSerializer(data=comment_data)
        is_valid = serializer.is_valid()
        if not is_valid:
            err = serializer.errors
            raise ValueError(
                f"[{self.file_path}] comments serializer failed: {err}"
            )

        comments = Comments(youtube_id=serializer.data["youtube_id"])
        comments.build_json()
        if not comments.json_data:
            comments.json_data = dict(serializer.data)

        comments.upload_comments()
