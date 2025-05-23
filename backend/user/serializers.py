"""serializer for account model"""

# pylint: disable=abstract-method

from common.src.helper import get_stylesheets
from rest_framework import serializers
from user.models import Account
from video.src.constants import OrderEnum, SortEnum


class AccountSerializer(serializers.ModelSerializer):
    """serialize account"""

    class Meta:
        model = Account
        fields = (
            "id",
            "name",
            "is_superuser",
            "is_staff",
            "groups",
            "user_permissions",
            "last_login",
        )


class UserMeConfigSerializer(serializers.Serializer):
    """serialize user me config"""

    stylesheet = serializers.ChoiceField(choices=get_stylesheets())
    page_size = serializers.IntegerField()
    sort_by = serializers.ChoiceField(choices=SortEnum.names())
    sort_order = serializers.ChoiceField(choices=OrderEnum.values())
    view_style_home = serializers.ChoiceField(
        choices=["grid", "list", "table"]
    )
    view_style_channel = serializers.ChoiceField(choices=["grid", "list"])
    view_style_downloads = serializers.ChoiceField(choices=["grid", "list"])
    view_style_playlist = serializers.ChoiceField(choices=["grid", "list"])
    grid_items = serializers.IntegerField(max_value=7, min_value=3)
    hide_watched = serializers.BooleanField()
    file_size_unit = serializers.ChoiceField(choices=["binary", "metric"])
    show_ignored_only = serializers.BooleanField()
    show_subed_only = serializers.BooleanField()
    show_help_text = serializers.BooleanField()


class LoginSerializer(serializers.Serializer):
    """serialize login"""

    username = serializers.CharField()
    password = serializers.CharField()
    remember_me = serializers.ChoiceField(choices=["on", "off"], default="off")
