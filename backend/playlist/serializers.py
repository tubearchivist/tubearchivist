"""playlist serializers"""

# pylint: disable=abstract-method

from common.serializers import PaginationSerializer
from rest_framework import serializers


class PlaylistEntrySerializer(serializers.Serializer):
    """serialize single playlist entry"""

    youtube_id = serializers.CharField()
    title = serializers.CharField()
    uploader = serializers.CharField()
    idx = serializers.IntegerField()
    downloaded = serializers.BooleanField()


class PlaylistSerializer(serializers.Serializer):
    """serialize playlist"""

    playlist_active = serializers.BooleanField()
    playlist_channel = serializers.CharField()
    playlist_channel_id = serializers.CharField()
    playlist_description = serializers.CharField()
    playlist_entries = PlaylistEntrySerializer(many=True)
    playlist_id = serializers.CharField()
    playlist_last_refresh = serializers.CharField()
    playlist_name = serializers.CharField()
    playlist_subscribed = serializers.BooleanField()
    playlist_sort_order = serializers.ChoiceField(choices=["top", "bottom"])
    playlist_thumbnail = serializers.CharField()
    playlist_type = serializers.ChoiceField(choices=["regular", "custom"])
    _index = serializers.CharField(required=False)
    _score = serializers.IntegerField(required=False)


class PlaylistListSerializer(serializers.Serializer):
    """serialize list of playlists"""

    data = PlaylistSerializer(many=True)
    paginate = PaginationSerializer()


class PlaylistListQuerySerializer(serializers.Serializer):
    """serialize playlist list query params"""

    channel = serializers.CharField(required=False)
    subscribed = serializers.BooleanField(required=False, allow_null=True)
    type = serializers.ChoiceField(
        choices=["regular", "custom"], required=False
    )
    page = serializers.IntegerField(required=False)


class PlaylistSingleAddSerializer(serializers.Serializer):
    """single item to add"""

    playlist_id = serializers.CharField()
    playlist_subscribed = serializers.ChoiceField(choices=[True])


class PlaylistBulkAddSerializer(serializers.Serializer):
    """bulk add playlists serializers"""

    data = PlaylistSingleAddSerializer(many=True)


class PlaylistSingleUpdate(serializers.Serializer):
    """update state of single playlist"""

    playlist_subscribed = serializers.BooleanField(required=False)
    playlist_sort_order = serializers.ChoiceField(
        choices=["top", "bottom"], required=False
    )


class PlaylistListCustomPostSerializer(serializers.Serializer):
    """serialize list post custom playlist"""

    playlist_name = serializers.CharField()


class PlaylistCustomPostSerializer(serializers.Serializer):
    """serialize playlist custom action"""

    action = serializers.ChoiceField(
        choices=["create", "remove", "up", "down", "top", "bottom"]
    )
    video_id = serializers.CharField()


class PlaylistDeleteQuerySerializer(serializers.Serializer):
    """serialize playlist delete query params"""

    delete_videos = serializers.BooleanField(required=False)
