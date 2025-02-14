"""serializers for stats"""

# pylint: disable=abstract-method

from rest_framework import serializers


class VideoStatsItemSerializer(serializers.Serializer):
    """serialize video stats item"""

    doc_count = serializers.IntegerField()
    media_size = serializers.IntegerField()
    duration = serializers.IntegerField()
    duration_str = serializers.CharField()


class VideoStatsSerializer(serializers.Serializer):
    """serialize video stats"""

    doc_count = serializers.IntegerField()
    media_size = serializers.IntegerField()
    duration = serializers.IntegerField()
    duration_str = serializers.CharField()
    type_videos = VideoStatsItemSerializer(allow_null=True)
    type_shorts = VideoStatsItemSerializer(allow_null=True)
    type_streams = VideoStatsItemSerializer(allow_null=True)
    active_true = VideoStatsItemSerializer(allow_null=True)
    active_false = VideoStatsItemSerializer(allow_null=True)


class ChannelStatsSerializer(serializers.Serializer):
    """serialize channel stats"""

    doc_count = serializers.IntegerField(allow_null=True)
    active_true = serializers.IntegerField(allow_null=True)
    active_false = serializers.IntegerField(allow_null=True)
    subscribed_true = serializers.IntegerField(allow_null=True)
    subscribed_false = serializers.IntegerField(allow_null=True)


class PlaylistStatsSerializer(serializers.Serializer):
    """serialize playlists stats"""

    doc_count = serializers.IntegerField(allow_null=True)
    active_true = serializers.IntegerField(allow_null=True)
    active_false = serializers.IntegerField(allow_null=True)
    subscribed_false = serializers.IntegerField(allow_null=True)
    subscribed_true = serializers.IntegerField(allow_null=True)


class DownloadStatsSerializer(serializers.Serializer):
    """serialize download stats"""

    pending = serializers.IntegerField(allow_null=True)
    ignore = serializers.IntegerField(allow_null=True)
    pending_videos = serializers.IntegerField(allow_null=True)
    pending_shorts = serializers.IntegerField(allow_null=True)
    pending_streams = serializers.IntegerField(allow_null=True)


class WatchTotalStatsSerializer(serializers.Serializer):
    """serialize total watch stats"""

    duration = serializers.IntegerField()
    duration_str = serializers.CharField()
    items = serializers.IntegerField()


class WatchItemStatsSerializer(serializers.Serializer):
    """serialize watch item stats"""

    duration = serializers.IntegerField()
    duration_str = serializers.CharField()
    progress = serializers.FloatField()
    items = serializers.IntegerField()


class WatchStatsSerializer(serializers.Serializer):
    """serialize watch stats"""

    total = WatchTotalStatsSerializer(allow_null=True)
    unwatched = WatchItemStatsSerializer(allow_null=True)
    watched = WatchItemStatsSerializer(allow_null=True)


class DownloadHistItemSerializer(serializers.Serializer):
    """serialize download hist item"""

    date = serializers.CharField()
    count = serializers.IntegerField()
    media_size = serializers.IntegerField()


class BiggestChannelQuerySerializer(serializers.Serializer):
    """serialize biggest channel query"""

    order = serializers.ChoiceField(
        choices=["doc_count", "duration", "media_size"], default="doc_count"
    )


class BiggestChannelItemSerializer(serializers.Serializer):
    """serialize biggest channel item"""

    id = serializers.CharField()
    name = serializers.CharField()
    doc_count = serializers.IntegerField()
    duration = serializers.IntegerField()
    duration_str = serializers.CharField()
    media_size = serializers.IntegerField()
