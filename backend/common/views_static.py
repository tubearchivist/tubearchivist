"""static media serving endpoints"""

import mimetypes
from pathlib import Path
from typing import Literal

from common.serializers import ErrorResponseSerializer
from common.src.env_settings import EnvironmentSettings
from common.src.streaming import RangedFileResponse
from common.views_base import StaticAuthBaseView
from django.http import HttpResponse
from download.src.thumbnails import ThumbManager
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
)
from rest_framework.response import Response

ERROR_RESPONSES = {
    400: OpenApiResponse(ErrorResponseSerializer(), description="Bad request"),
    404: OpenApiResponse(ErrorResponseSerializer(), description="Not found"),
}


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

    @extend_schema(
        operation_id="media_stream",
        parameters=[
            OpenApiParameter(
                name="Range",
                type=str,
                location=OpenApiParameter.HEADER,
                description="Single byte range, for example bytes=0-1023",
            )
        ],
        responses={
            (200, "video/mp4"): OpenApiTypes.BINARY,
            (206, "video/mp4"): OpenApiTypes.BINARY,
            **ERROR_RESPONSES,
            416: OpenApiResponse(description="Range not satisfiable"),
        },
    )
    def get(self, request, channel_id, video_id):
        """get media stream, handle ranged byte request"""
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


class SubtitleView(StaticAuthBaseView):
    """resolves to /media/subtitle/<channel_id>/<video_id>.<lang>.vtt
    authenticated subtitle serving.
    public read with DISABLE_STATIC_AUTH
    GET: get subtitle
    """

    def get_subtitle_path(
        self, channel_id: str, video_id: str, lang: str
    ) -> Path:
        """get subtitle path"""
        self.validate_channel_id(channel_id)
        self.validate_video_id(video_id)
        self.validate_subtitle_lang(lang)

        return Path(
            EnvironmentSettings.MEDIA_DIR, channel_id, f"{video_id}.{lang}.vtt"
        )

    @extend_schema(
        operation_id="media_subtitle",
        responses={
            (200, "text/vtt"): OpenApiTypes.BINARY,
            **ERROR_RESPONSES,
        },
    )
    def get(self, request, channel_id, video_id, lang):
        """get subtitle file"""
        try:
            subtitle_path = self.get_subtitle_path(channel_id, video_id, lang)
        except ValueError as path_err:
            error = ErrorResponseSerializer({"error": str(path_err)})
            return Response(error.data, status=400)

        if not subtitle_path.is_file():
            error = ErrorResponseSerializer({"error": "file not found"})
            return Response(error.data, status=404)

        content = subtitle_path.read_bytes()
        response = HttpResponse(content, content_type="text/vtt")
        response["Cache-Control"] = self.CACHE_CONTROL

        return response


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

    @extend_schema(
        operation_id="media_video_thumbnail",
        responses={
            (200, "image/jpeg"): OpenApiTypes.BINARY,
            **ERROR_RESPONSES,
        },
    )
    def get(self, request, video_id):
        """get video thumb"""
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
        response["Cache-Control"] = self.CACHE_CONTROL

        return response


class ChannelArtView(StaticAuthBaseView):
    """resolves to /media/thumb/channel/<channel_id>/<art-type>.jpg
    authenticated channel art endpoint
    public read with DISABLE_STATIC_AUTH
    GET: get thumbnail
    """

    def get_art_path(
        self, channel_id: str, art_type: Literal["thumb", "banner", "tvart"]
    ) -> Path:
        """get path"""
        self.validate_channel_id(channel_id)
        self.validate_channel_art_type(art_type)
        return Path(ThumbManager(channel_id).channel_art_path(art_type))

    @extend_schema(
        operation_id="media_channel_art",
        responses={
            (200, "image/jpeg"): OpenApiTypes.BINARY,
            **ERROR_RESPONSES,
        },
    )
    def get(self, request, channel_id, art_type):
        """get channel artwork"""
        try:
            art_path = self.get_art_path(channel_id, art_type=art_type)
        except ValueError as path_err:
            error = ErrorResponseSerializer({"error": str(path_err)})
            return Response(error.data, status=400)

        if not art_path.is_file():
            error = ErrorResponseSerializer({"error": "file not found"})
            return Response(error.data, status=404)

        content = art_path.read_bytes()
        response = HttpResponse(content, content_type="image/jpeg")
        response["Cache-Control"] = self.CACHE_CONTROL

        return response


class PlaylistThumbView(StaticAuthBaseView):
    """resolves to /media/thumb/playlist/<playlist_id>.jpg
    authenticated playlist thumb endpoint
    public read with DISABLE_STATIC_AUTH
    GET: get thumbnail
    """

    def get_thumb_path(self, playlist_id: str) -> Path:
        """get path"""
        self.validate_playlist_id(playlist_id)
        return Path(ThumbManager(item_id=playlist_id).playlist_art_path())

    @extend_schema(
        operation_id="media_playlist_thumbnail",
        responses={
            (200, "image/jpeg"): OpenApiTypes.BINARY,
            **ERROR_RESPONSES,
        },
    )
    def get(self, request, playlist_id):
        """get playlist thumb"""
        try:
            thumb_path = self.get_thumb_path(playlist_id)
        except ValueError as path_err:
            error = ErrorResponseSerializer({"error": str(path_err)})
            return Response(error.data, status=400)

        if not thumb_path.is_file():
            error = ErrorResponseSerializer({"error": "file not found"})
            return Response(error.data, status=404)

        content = thumb_path.read_bytes()
        response = HttpResponse(content, content_type="image/jpeg")
        response["Cache-Control"] = self.CACHE_CONTROL

        return response
