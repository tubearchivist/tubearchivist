"""common serializers"""

# pylint: disable=abstract-method

from rest_framework import serializers


class ValidateUnknownFieldsMixin:
    """
    Mixin to validate and reject unknown fields in a serializer.
    """

    def to_internal_value(self, data):
        """check expected keys"""
        allowed_fields = set(self.fields.keys())
        input_fields = set(data.keys())

        # Find unknown fields
        unknown_fields = input_fields - allowed_fields
        if unknown_fields:
            raise serializers.ValidationError(
                {"error": f"Unknown fields: {', '.join(unknown_fields)}"}
            )

        return super().to_internal_value(data)


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


class AsyncTaskResponseSerializer(serializers.Serializer):
    """serialize new async task"""

    message = serializers.CharField()
    task_id = serializers.CharField()
    filename = serializers.CharField(required=False)
