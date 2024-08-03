"""serializer for account model"""

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
