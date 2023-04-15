"""extract metadata from video streams"""

import json
import subprocess
from os import stat


class DurationConverter:
    """
    using ffmpeg to get and parse duration from filepath
    """

    @staticmethod
    def get_sec(file_path):
        """read duration from file"""
        duration = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                file_path,
            ],
            capture_output=True,
            check=True,
        )
        duration_raw = duration.stdout.decode().strip()
        if duration_raw == "N/A":
            return 0

        duration_sec = int(float(duration_raw))
        return duration_sec

    @staticmethod
    def get_str(duration_sec):
        """takes duration in sec and returns clean string"""
        if not duration_sec:
            # failed to extract
            return "NA"

        hours = int(duration_sec // 3600)
        minutes = int((duration_sec - (hours * 3600)) // 60)
        secs = int(duration_sec - (hours * 3600) - (minutes * 60))

        duration_str = str()
        if hours:
            duration_str = str(hours).zfill(2) + ":"
        if minutes:
            duration_str = duration_str + str(minutes).zfill(2) + ":"
        else:
            duration_str = duration_str + "00:"
        duration_str = duration_str + str(secs).zfill(2)
        return duration_str


class MediaStreamExtractor:
    """extract stream metadata"""

    def __init__(self, media_path):
        self.media_path = media_path
        self.metadata = []

    def extract_metadata(self):
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

    def process_stream(self, stream):
        """parse stream to metadata"""
        codec_type = stream.get("codec_type")
        if codec_type == "video":
            self._extract_video_metadata(stream)
        elif codec_type == "audio":
            self._extract_audio_metadata(stream)
        else:
            return

    def _extract_video_metadata(self, stream):
        """parse video metadata"""
        if "bit_rate" not in stream:
            # is probably thumbnail
            return

        self.metadata.append(
            {
                "type": "video",
                "index": stream["index"],
                "codec": stream["codec_name"],
                "width": stream["width"],
                "height": stream["height"],
                "bitrate": int(stream["bit_rate"]),
            }
        )

    def _extract_audio_metadata(self, stream):
        """extract audio metadata"""
        self.metadata.append(
            {
                "type": "audio",
                "index": stream["index"],
                "codec": stream["codec_name"],
                "bitrate": int(stream["bit_rate"]),
            }
        )

    def get_file_size(self):
        """get filesize in bytes"""
        return stat(self.media_path).st_size
