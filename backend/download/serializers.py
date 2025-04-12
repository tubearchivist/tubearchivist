"""download serializers"""

# pylint: disable=abstract-method

from common.serializers import PaginationSerializer, ValidateUnknownFieldsMixin
from rest_framework import serializers
from video.src.constants import VideoTypeEnum


class DownloadItemSerializer(serializers.Serializer):
    """serialize download item"""

    auto_start = serializers.BooleanField()
    channel_id = serializers.CharField()
    channel_indexed = serializers.BooleanField(required=False)
    channel_name = serializers.CharField()
    duration = serializers.CharField()
    published = serializers.CharField()
    status = serializers.ChoiceField(choices=["pending", "ignore"])
    timestamp = serializers.IntegerField()
    title = serializers.CharField()
    vid_thumb_url = serializers.CharField()
    vid_type = serializers.ChoiceField(choices=VideoTypeEnum.values())
    youtube_id = serializers.CharField()
    message = serializers.CharField(required=False)
    _index = serializers.CharField(required=False)
    _score = serializers.IntegerField(required=False)


class DownloadListSerializer(serializers.Serializer):
    """serialize download list"""

    data = DownloadItemSerializer(many=True)
    paginate = PaginationSerializer()


class DownloadListQuerySerializer(
    ValidateUnknownFieldsMixin, serializers.Serializer
):
    """serialize query params for download list"""

    filter = serializers.ChoiceField(
        choices=["pending", "ignore"], required=False
    )
    channel = serializers.CharField(required=False, help_text="channel ID")
    page = serializers.IntegerField(required=False)


class DownloadListQueueDeleteQuerySerializer(serializers.Serializer):
    """serialize bulk delete download queue query string"""

    filter = serializers.ChoiceField(choices=["pending", "ignore"])


class AddDownloadItemSerializer(serializers.Serializer):
    """serialize single item to add"""

    youtube_id = serializers.CharField()
    status = serializers.ChoiceField(choices=["pending", "ignore-force"])


class AddToDownloadListSerializer(serializers.Serializer):
    """serialize add to download queue data"""

    data = AddDownloadItemSerializer(many=True)


class AddToDownloadQuerySerializer(serializers.Serializer):
    """add to queue query serializer"""

    autostart = serializers.BooleanField(required=False)


class DownloadQueueItemUpdateSerializer(serializers.Serializer):
    """update single download queue item"""

    status = serializers.ChoiceField(
        choices=["pending", "ignore", "ignore-force", "priority"]
    )


class DownloadAggBucketSerializer(serializers.Serializer):
    """serialize bucket"""

    key = serializers.ListField(child=serializers.CharField())
    key_as_string = serializers.CharField()
    doc_count = serializers.IntegerField()


class DownloadAggsSerializer(serializers.Serializer):
    """serialize download channel bucket aggregations"""

    doc_count_error_upper_bound = serializers.IntegerField()
    sum_other_doc_count = serializers.IntegerField()
    buckets = DownloadAggBucketSerializer(many=True)
