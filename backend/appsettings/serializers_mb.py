"""membership platform serializers"""

# pylint: disable=abstract-method

from rest_framework import serializers


class MembershipUserSerializer(serializers.Serializer):
    """serialize user"""

    id = serializers.IntegerField()
    username = serializers.CharField()


class SponsortierSerializer(serializers.Serializer):
    """serialize sponsor tier"""

    tier_id = serializers.IntegerField()
    name = serializers.CharField()
    description = serializers.CharField()
    max_subs = serializers.IntegerField()


class MembershipProfileSerializer(serializers.Serializer):
    """serialize membership profile"""

    id = serializers.IntegerField()
    user = MembershipUserSerializer()
    sponsor_tier = SponsortierSerializer()
    subscription_count = serializers.IntegerField()
    subscription_is_max = serializers.BooleanField()
