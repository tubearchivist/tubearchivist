"""serializer for tasks"""

from rest_framework import serializers
from task.models import CustomPeriodicTask


class CustomPeriodicTaskSerializer(serializers.ModelSerializer):
    """serialize CustomPeriodicTask"""

    schedule = serializers.CharField(source="schedule_parsed")
    schedule_human = serializers.CharField(source="crontab.human_readable")
    last_run_at = serializers.DateTimeField()
    config = serializers.DictField(source="task_config")

    class Meta:
        model = CustomPeriodicTask
        fields = [
            "name",
            "schedule",
            "schedule_human",
            "last_run_at",
            "config",
        ]
