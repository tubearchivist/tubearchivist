"""serializer for account model"""

# pylint: disable=abstract-method

from rest_framework import serializers
from user.models import Account


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

    stylesheet = serializers.CharField()
    page_size = serializers.IntegerField()
    sort_by = serializers.ChoiceField(
        choices=[
            "published",
            "downloaded",
            "views",
            "likes",
            "duration",
            "filesize",
        ]
    )
    sort_order = serializers.ChoiceField(choices=["asc", "desc"])
    view_style_home = serializers.ChoiceField(choices=["grid", "list"])
    view_style_channel = serializers.ChoiceField(choices=["grid", "list"])
    view_style_downloads = serializers.ChoiceField(choices=["grid", "list"])
    view_style_playlist = serializers.ChoiceField(choices=["grid", "list"])
    grid_items = serializers.IntegerField()
    hide_watched = serializers.BooleanField()
    show_ignored_only = serializers.BooleanField()
    show_subed_only = serializers.BooleanField()
    show_help_text = serializers.BooleanField()


class LoginSerializer(serializers.Serializer):
    """serialize login"""

    username = serializers.CharField()
    password = serializers.CharField()
    remember_me = serializers.ChoiceField(choices=["on", "off"], default="off")
