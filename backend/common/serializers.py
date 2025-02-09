"""common serializers"""

# pylint: disable=abstract-method

from rest_framework import serializers


class ErrorResponseSerializer(serializers.Serializer):
    """error message"""

    error = serializers.CharField()


class PaginationSerializer(serializers.Serializer):
    """serialize paginate response"""

    page_size = serializers.IntegerField()
    page_from = serializers.IntegerField()
    prev_pages = serializers.ListField(
        child=serializers.IntegerField(), allow_null=True
    )
    current_page = serializers.IntegerField()
    max_hits = serializers.BooleanField()
    params = serializers.CharField()
    last_page = serializers.BooleanField()
    next_pages = serializers.ListField(
        child=serializers.IntegerField(), allow_null=True
    )
    total_hits = serializers.IntegerField()
