"""static media serving endpoints"""

import mimetypes
import re
from pathlib import Path

from common.serializers import ErrorResponseSerializer
from common.src.env_settings import EnvironmentSettings
from common.src.streaming import RangedFileResponse
from common.views_base import StaticAuthBaseView
from rest_framework.response import Response


class MediaStreamView(StaticAuthBaseView):
    """resolves to /media/stream/<channel_id>/<video_id>/
    Authenticated media streaming endpoint.
    GET: get media partial range or complete
    """

    CHANNEL_ID_REG = re.compile(r"UC[A-Za-z0-9_-]{22}")
    VIDEO_ID_REG = re.compile(r"[A-Za-z0-9_-]{11}")

    def get_media_path(self, channel_id: str, video_id: str) -> Path:
        """build media path, protect path access"""
        if not self.CHANNEL_ID_REG.fullmatch(channel_id):
            raise ValueError("invalid channel ID")

        if not self.VIDEO_ID_REG.fullmatch(video_id):
            raise ValueError("invalid video ID")

        return Path(
            EnvironmentSettings.MEDIA_DIR, channel_id, f"{video_id}.mp4"
        )

    def get(self, request, channel_id, video_id):
        """get request"""
        try:
            path = self.get_media_path(channel_id, video_id)
        except ValueError as path_err:
            error = ErrorResponseSerializer({"error": str(path_err)})
            return Response(error.data, status=400)

        if not path.is_file():
            error = ErrorResponseSerializer({"error": "file not found"})
            return Response(error.data, status=404)

        content_type, _ = mimetypes.guess_type(path.name)

        return RangedFileResponse(
            request=request,
            path=path,
            content_type=content_type or "application/octet-stream",
        )
