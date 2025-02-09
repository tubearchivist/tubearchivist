"""channel serializers"""

# pylint: disable=abstract-method

from common.serializers import PaginationSerializer
from rest_framework import serializers


class ChannelOverwriteSerializer(serializers.Serializer):
    """serialize channel overwrites"""

    download_format = serializers.CharField(required=False, allow_null=True)
    autodelete_days = serializers.IntegerField(required=False, allow_null=True)
    index_playlists = serializers.BooleanField(required=False, allow_null=True)
    integrate_sponsorblock = serializers.BooleanField(
        required=False, allow_null=True
    )
    subscriptions_channel_size = serializers.IntegerField(
        required=False, allow_null=True
    )
    subscriptions_live_channel_size = serializers.IntegerField(
        required=False, allow_null=True
    )
    subscriptions_shorts_channel_size = serializers.IntegerField(
        required=False, allow_null=True
    )

    def to_internal_value(self, data):
        """Override this method to detect unknown fields."""
        allowed_fields = set(self.fields.keys())
        input_fields = set(data.keys())

        unknown_fields = input_fields - allowed_fields

        if unknown_fields:
            raise serializers.ValidationError(
                {"error": f"Unknown fields: {', '.join(unknown_fields)}"}
            )

        return super().to_internal_value(data)


class ChannelSerializer(serializers.Serializer):
    """serialize channel"""

    channel_id = serializers.CharField()
    channel_active = serializers.BooleanField()
    channel_banner_url = serializers.CharField()
    channel_thumb_url = serializers.CharField()
    channel_tvart_url = serializers.CharField()
    channel_description = serializers.CharField()
    channel_last_refresh = serializers.CharField()
    channel_name = serializers.CharField()
    channel_overwrites = ChannelOverwriteSerializer(required=False)
    channel_subs = serializers.IntegerField()
    channel_subscribed = serializers.BooleanField()
    channel_tags = serializers.ListField(child=serializers.CharField())
    channel_views = serializers.IntegerField()
    _index = serializers.CharField(required=False)
    _score = serializers.IntegerField(required=False)


class ChannelListSerializer(serializers.Serializer):
    """serialize channel list"""

    data = ChannelSerializer(many=True)
    paginate = PaginationSerializer()


class ChannelListQuerySerializer(serializers.Serializer):
    """serialize list query"""

    filter = serializers.ChoiceField(choices=["subscribed"], required=False)


class ChannelUpdateSerializer(serializers.Serializer):
    """update channel"""

    channel_subscribed = serializers.BooleanField(required=False)
    channel_overwrites = ChannelOverwriteSerializer(required=False)


class ChannelAggBucketSerializer(serializers.Serializer):
    """serialize channel agg bucket"""

    value = serializers.IntegerField()
    value_str = serializers.CharField(required=False)


class ChannelAggSerializer(serializers.Serializer):
    """serialize channel aggregation"""

    total_items = ChannelAggBucketSerializer()
    total_size = ChannelAggBucketSerializer()
    total_duration = ChannelAggBucketSerializer()


class ChannelNavSerializer(serializers.Serializer):
    """serialize channel navigation"""

    has_pending = serializers.BooleanField()
    has_playlists = serializers.BooleanField()
    has_videos = serializers.BooleanField()
    has_streams = serializers.BooleanField()
    has_shorts = serializers.BooleanField()


class ChannelSearchQuerySerializer(serializers.Serializer):
    """serialize query parameters for searching"""

    q = serializers.CharField()
