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
    subscribed = serializers.BooleanField(required=False)
    type = serializers.ChoiceField(
        choices=["regular", "custom"], required=False
    )
