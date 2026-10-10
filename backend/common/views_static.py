"""static media serving endpoints"""

import mimetypes
from pathlib import Path

from common.serializers import ErrorResponseSerializer
from common.src.env_settings import EnvironmentSettings
from common.src.streaming import RangedFileResponse
from common.views_base import StaticAuthBaseView
from django.http import HttpResponse
from download.src.thumbnails import ThumbManager
from rest_framework.response import Response


class MediaStreamView(StaticAuthBaseView):
    """resolves to /media/stream/<channel_id>/<video_id>.mp4
    authenticated media streaming endpoint.
    public read with DISABLE_STATIC_AUTH
    GET: get media partial range or complete
    """

    def get_media_path(self, channel_id: str, video_id: str) -> Path:
        """build media path, protect path access"""
        self.validate_channel_id(channel_id)
        self.validate_video_id(video_id)

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


class VideoThumbView(StaticAuthBaseView):
    """resolves to /media/thumb/video/<video_id>.jpg
    authenticated video thumb endpoint
    public read with DISABLE_STATIC_AUTH
    GET: get thumbnail
    """

    def get_thumb_path(self, video_id: str) -> Path:
        """get path"""
        self.validate_video_id(video_id)
        return Path(
            ThumbManager(item_id=video_id).vid_thumb_path(absolute=True)
        )

    def get(self, request, video_id):
        """get thumb"""
        try:
            thumb_path = self.get_thumb_path(video_id)
        except ValueError as path_err:
            error = ErrorResponseSerializer({"error": str(path_err)})
            return Response(error.data, status=400)

        if not thumb_path.is_file():
            error = ErrorResponseSerializer({"error": "file not found"})
            return Response(error.data, status=404)

        content = thumb_path.read_bytes()
        response = HttpResponse(content, content_type="image/jpeg")
        response["Cache-Control"] = "public, max-age=3600"

        return response
