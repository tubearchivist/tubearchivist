"""appsettings erializers"""

# pylint: disable=abstract-method

from common.serializers import ValidateUnknownFieldsMixin
from rest_framework import serializers


class BackupFileSerializer(serializers.Serializer):
    """serialize backup file"""

    filename = serializers.CharField()
    file_path = serializers.CharField()
    file_size = serializers.IntegerField()
    timestamp = serializers.CharField()
    reason = serializers.CharField()


class AppConfigSubSerializer(
    ValidateUnknownFieldsMixin, serializers.Serializer
):
    """serialize app config subscriptions"""

    channel_size = serializers.IntegerField(required=False, allow_null=True)
    live_channel_size = serializers.IntegerField(
        required=False, allow_null=True
    )
    shorts_channel_size = serializers.IntegerField(
        required=False, allow_null=True
    )
    playlist_size = serializers.IntegerField(required=False, allow_null=True)
    auto_start = serializers.BooleanField(required=False)
    extract_flat = serializers.BooleanField(required=False)


class AppConfigDownloadsSerializer(
    ValidateUnknownFieldsMixin, serializers.Serializer
):
    """serialize app config downloads config"""

    limit_speed = serializers.IntegerField(allow_null=True)
    sleep_interval = serializers.IntegerField(allow_null=True)
    autodelete_days = serializers.IntegerField(allow_null=True)
    format = serializers.CharField(allow_null=True)
    format_sort = serializers.CharField(allow_null=True)
    add_metadata = serializers.BooleanField()
    add_thumbnail = serializers.BooleanField()
    subtitle = serializers.CharField(allow_null=True)
    subtitle_source = serializers.ChoiceField(
        choices=["auto", "user"], allow_null=True
    )
    subtitle_index = serializers.BooleanField()
    comment_max = serializers.CharField(allow_null=True)
    comment_sort = serializers.ChoiceField(
        choices=["top", "new"], allow_null=True
    )
    cookie_import = serializers.BooleanField()
    potoken = serializers.BooleanField()
    throttledratelimit = serializers.IntegerField(allow_null=True)
    extractor_lang = serializers.CharField(allow_null=True)
    integrate_ryd = serializers.BooleanField()
    integrate_sponsorblock = serializers.BooleanField()


class AppConfigAppSerializer(
    ValidateUnknownFieldsMixin, serializers.Serializer
):
    """serialize app config"""

    enable_snapshot = serializers.BooleanField()
    enable_cast = serializers.BooleanField()


class AppConfigSerializer(ValidateUnknownFieldsMixin, serializers.Serializer):
    """serialize appconfig"""

    subscriptions = AppConfigSubSerializer(required=False)
    downloads = AppConfigDownloadsSerializer(required=False)
    application = AppConfigAppSerializer(required=False)


class CookieValidationSerializer(serializers.Serializer):
    """serialize cookie validation response"""

    cookie_enabled = serializers.BooleanField()
    status = serializers.BooleanField(required=False)
    validated = serializers.IntegerField(required=False)
    validated_str = serializers.CharField(required=False)


class CookieUpdateSerializer(serializers.Serializer):
    """serialize cookie to update"""

    cookie = serializers.CharField()


class PoTokenSerializer(serializers.Serializer):
    """serialize PO token"""

    potoken = serializers.CharField()


class SnapshotItemSerializer(serializers.Serializer):
    """serialize snapshot response"""

    id = serializers.CharField()
    state = serializers.CharField()
    es_version = serializers.CharField()
    start_date = serializers.CharField()
    end_date = serializers.CharField()
    end_stamp = serializers.IntegerField()
    duration_s = serializers.IntegerField()


class SnapshotListSerializer(serializers.Serializer):
    """serialize snapshot list response"""

    next_exec = serializers.IntegerField()
    next_exec_str = serializers.CharField()
    expire_after = serializers.CharField()
    snapshots = SnapshotItemSerializer(many=True)


class SnapshotCreateResponseSerializer(serializers.Serializer):
    """serialize new snapshot creating response"""

    snapshot_name = serializers.CharField()


class SnapshotRestoreResponseSerializer(serializers.Serializer):
    """serialize snapshot restore response"""

    accepted = serializers.BooleanField()


class TokenResponseSerializer(serializers.Serializer):
    """serialize token response"""

    token = serializers.CharField(allow_null=True)
