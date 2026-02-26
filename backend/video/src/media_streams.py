"""extract metadata from video streams"""

import json
import subprocess
from os import stat


class MediaStreamExtractor:
    """extract stream metadata"""

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
        tags = stream.get("tags", {})

        # Bitrate: prefer stream-level, fall back to BPS tag (common in MKV)
        bitrate_raw = stream.get("bit_rate")
        if not bitrate_raw:
            bps_tag = tags.get("BPS") or tags.get("BPS-eng") or tags.get("NUMBER_OF_BYTES")
            if bps_tag:
                try:
                    bitrate_raw = int(bps_tag)
                except (TypeError, ValueError):
                    bitrate_raw = 0
            else:
                bitrate_raw = 0

        language = (
            tags.get("language")
            or tags.get("LANGUAGE")
            or tags.get("Language")
            or tags.get("lang")
            or tags.get("LANG")
            or None
        )
        # Normalise "und" (undetermined) to None
        if isinstance(language, str):
            language = language.strip()

        if language and language.lower() == "und":
            language = None

        track_title = (
            tags.get("title")
            or tags.get("TITLE")
            or tags.get("Title")
            or tags.get("handler_name")
            or tags.get("HANDLER_NAME")
            or None
        )
        track_title = self._clean_audio_title(track_title)

        # Channels: prefer channel_layout label, fall back to channel count
        channel_layout = stream.get("channel_layout")
        channels = stream.get("channels")

        self.metadata.append(
            {
                "bitrate": int(bitrate_raw),
                "codec": stream.get("codec_name", "undefined"),
                "index": stream["index"],
                "type": "audio",
                "language": language,
                "title": track_title,
                "channels": channels,
                "channel_layout": channel_layout,
            }
        )

    @staticmethod
    def _clean_audio_title(track_title: str | None) -> str | None:
        """remove noisy/generic audio titles that aren't useful for UI labels"""
        if not track_title:
            return None

        cleaned = track_title.strip()
        if not cleaned:
            return None

        lower = cleaned.lower()
        noisy_titles = {
            "iso media file produced by google inc.",
            "soundhandler",
            "iso media",
        }

        if lower in noisy_titles:
            return None

        return cleaned

    def get_file_size(self) -> int:
        """get filesize in bytes"""
        return stat(self.media_path).st_size
