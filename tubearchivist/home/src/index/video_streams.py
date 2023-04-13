"""extract metadata from video streams"""

import subprocess


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

        hours = duration_sec // 3600
        minutes = (duration_sec - (hours * 3600)) // 60
        secs = duration_sec - (hours * 3600) - (minutes * 60)

        duration_str = str()
        if hours:
            duration_str = str(hours).zfill(2) + ":"
        if minutes:
            duration_str = duration_str + str(minutes).zfill(2) + ":"
        else:
            duration_str = duration_str + "00:"
        duration_str = duration_str + str(secs).zfill(2)
        return duration_str
