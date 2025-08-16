"""video serializers"""

# pylint: disable=abstract-method

from channel.serializers import ChannelSerializer
from common.serializers import PaginationSerializer
from rest_framework import serializers
from video.src.constants import OrderEnum, SortEnum, VideoTypeEnum, WatchedEnum


class PlayerSerializer(serializers.Serializer):
    """serialize player"""

    watched = serializers.BooleanField()
    watched_date = serializers.IntegerField(required=False)
    duration = serializers.IntegerField()
    duration_str = serializers.CharField()
    progress = serializers.FloatField(required=False)
    position = serializers.FloatField(required=False)


class SponsorBlockSegmentSerializer(serializers.Serializer):
    """serialize sponsorblock segment"""

    actionType = serializers.CharField()
    videoDuration = serializers.FloatField()
    segment = serializers.ListField(child=serializers.FloatField())
    votes = serializers.IntegerField()
    category = serializers.CharField()
    UUID = serializers.CharField()
    locked = serializers.IntegerField()


class SponsorBlockSerializer(serializers.Serializer):
    """serialize sponsorblock"""

    is_enabled = serializers.BooleanField()
    last_refresh = serializers.IntegerField()
    has_unlocked = serializers.BooleanField(required=False)
    segments = SponsorBlockSegmentSerializer(many=True)


class StatsSerializer(serializers.Serializer):
    """serialize stats"""

    like_count = serializers.IntegerField(required=False)
    average_rating = serializers.FloatField(required=False)
    view_count = serializers.IntegerField(required=False)
    dislike_count = serializers.IntegerField(required=False)


class StreamItemSerializer(serializers.Serializer):
    """serialize stream item"""

    index = serializers.IntegerField()
    codec = serializers.CharField()
    bitrate = serializers.IntegerField()
    type = serializers.ChoiceField(choices=["video", "audio"])
    width = serializers.IntegerField(required=False)
    height = serializers.IntegerField(required=False)


class SubtitleItemSerializer(serializers.Serializer):
    """serialize subtitle item"""

    ext = serializers.ChoiceField(choices=["json3"])
    name = serializers.CharField()
    source = serializers.ChoiceField(choices=["user", "auto"])
    lang = serializers.CharField()
    media_url = serializers.CharField()
    url = serializers.URLField()


class VideoSerializer(serializers.Serializer):
    """serialize video item"""

    active = serializers.BooleanField()
    category = serializers.ListField(child=serializers.CharField())
    channel = ChannelSerializer()
    comment_count = serializers.IntegerField(allow_null=True)
    date_downloaded = serializers.IntegerField()
    description = serializers.CharField()
    media_size = serializers.IntegerField()
    media_url = serializers.CharField()
    player = PlayerSerializer()
    playlist = serializers.ListField(child=serializers.CharField())
    published = serializers.CharField()
    sponsorblock = SponsorBlockSerializer(allow_null=True)
    stats = StatsSerializer()
    streams = StreamItemSerializer(many=True)
    subtitles = SubtitleItemSerializer(many=True)
    tags = serializers.ListField(child=serializers.CharField())
    title = serializers.CharField()
    vid_last_refresh = serializers.CharField()
    vid_thumb_url = serializers.CharField()
    vid_type = serializers.ChoiceField(choices=VideoTypeEnum.values_known())
    youtube_id = serializers.CharField()
    _index = serializers.CharField(required=False)
    _score = serializers.FloatField(required=False)


class VideoListSerializer(serializers.Serializer):
    """serialize video list"""

    data = VideoSerializer(many=True)
    paginate = PaginationSerializer()


class VideoListQuerySerializer(serializers.Serializer):
    """serialize query for video list"""

    playlist = serializers.CharField(required=False)
    channel = serializers.CharField(required=False)
    watch = serializers.ChoiceField(
        choices=WatchedEnum.values(), required=False, allow_null=True
    )
    sort = serializers.ChoiceField(choices=SortEnum.names(), required=False)
    order = serializers.ChoiceField(choices=OrderEnum.values(), required=False)
    type = serializers.ChoiceField(
        choices=VideoTypeEnum.values_known(), required=False
    )
    page = serializers.IntegerField(required=False)
    height = serializers.IntegerField(required=False)


class CommentThreadItemSerializer(serializers.Serializer):
    """serialize comment thread item"""

    comment_id = serializers.CharField()
    comment_text = serializers.CharField()
    comment_timestamp = serializers.IntegerField()
    comment_time_text = serializers.CharField()
    comment_likecount = serializers.IntegerField()
    comment_is_favorited = serializers.BooleanField()
    comment_author = serializers.CharField()
    comment_author_id = serializers.CharField()
    comment_author_thumbnail = serializers.URLField()
    comment_author_is_uploader = serializers.BooleanField()
    comment_parent = serializers.CharField()


class CommentItemSerializer(serializers.Serializer):
    """serialize comment item"""

    comment_id = serializers.CharField()
    comment_text = serializers.CharField()
    comment_timestamp = serializers.IntegerField()
    comment_time_text = serializers.CharField()
    comment_likecount = serializers.IntegerField()
    comment_is_favorited = serializers.BooleanField()
    comment_author = serializers.CharField()
    comment_author_id = serializers.CharField()
    comment_author_thumbnail = serializers.URLField()
    comment_author_is_uploader = serializers.BooleanField()
    comment_parent = serializers.CharField()
    comment_replies = CommentThreadItemSerializer(many=True)


class PlaylistNavMetaSerializer(serializers.Serializer):
    """serialize playlist nav meta"""

    current_idx = serializers.IntegerField()
    playlist_id = serializers.CharField()
    playlist_name = serializers.CharField()
    playlist_channel = serializers.CharField()


class PlaylistNavVideoSerializer(serializers.Serializer):
    """serialize video item on playlist nav"""

    youtube_id = serializers.CharField()
    title = serializers.CharField()
    uploader = serializers.CharField()
    idx = serializers.IntegerField()
    downloaded = serializers.BooleanField()
    vid_thumb = serializers.CharField()


class PlaylistNavItemSerializer(serializers.Serializer):
    """serialize nav on playlist"""

    playlist_meta = PlaylistNavMetaSerializer()
    playlist_previous = PlaylistNavVideoSerializer(allow_null=True)
    playlist_next = PlaylistNavVideoSerializer(allow_null=True)


class VideoProgressUpdateSerializer(serializers.Serializer):
    """serialize progress update data"""

    position = serializers.FloatField(default=0)
