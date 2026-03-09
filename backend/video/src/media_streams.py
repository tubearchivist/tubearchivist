"""extract metadata from video streams"""

import json
import subprocess
from os import stat


class MediaStreamExtractor:
    """extract stream metadata"""

    GENERIC_AUDIO_TITLES = {
        "soundhandler",
        "iso media file produced by google inc.",
    }

    def __init__(self, media_path):
        self.media_path = media_path
        self.metadata = []

    def extract_metadata(self) -> list[dict]:
        """entry point to extract metadata"""

        cmd = [
            "ffprobe",
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_streams",
            "-show_format",
            self.media_path,
        ]
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=False
        )

        if result.returncode != 0:
            return self.metadata

        streams = json.loads(result.stdout).get("streams")
        for stream in streams:
            self.process_stream(stream)

        return self.metadata

    def process_stream(self, stream) -> None:
        """parse stream to metadata"""
        codec_type = stream.get("codec_type")
        if codec_type == "video":
            self._extract_video_metadata(stream)
        elif codec_type == "audio":
            self._extract_audio_metadata(stream)

    def _extract_video_metadata(self, stream) -> None:
        """parse video metadata"""
        if "bit_rate" not in stream:
            # is probably thumbnail
            return

        self.metadata.append(
            {
                "bitrate": int(stream.get("bit_rate", 0)),
                "codec": stream["codec_name"],
                "height": stream["height"],
                "index": stream["index"],
                "type": "video",
                "width": stream["width"],
            }
        )

    def _extract_audio_metadata(self, stream) -> None:
        """extract audio metadata"""
        tags = stream.get("tags") or {}
        language = (
            tags.get("language")
            or tags.get("LANGUAGE")
            or stream.get("language")
        )
        title = (
            tags.get("title")
            or tags.get("handler_name")
            or tags.get("HANDLER_NAME")
        )
        if (
            isinstance(title, str)
            and title.strip().lower() in self.GENERIC_AUDIO_TITLES
        ):
            title = None

        self.metadata.append(
            {
                "bitrate": int(stream.get("bit_rate", 0)),
                "codec": stream.get("codec_name", "undefined"),
                "index": stream["index"],
                "language": language,
                "title": title,
                "type": "audio",
            }
        )

    def get_file_size(self) -> int:
        """get filesize in bytes"""
        return stat(self.media_path).st_size
