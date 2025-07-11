"""serializer for tasks"""

# pylint: disable=abstract-method

from rest_framework import serializers
from task.models import CustomPeriodicTask
from task.src.task_config import TASK_CONFIG


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


class TaskResultSerializer(serializers.Serializer):
    """serialize task result stored in redis"""

    status = serializers.ChoiceField(
        choices=[
            "PENDING",
            "STARTED",
            "SUCCESS",
            "FAILURE",
            "RETRY",
            "REVOKED",
        ]
    )
    result = serializers.CharField(allow_null=True)
    traceback = serializers.CharField(allow_null=True)
    date_done = serializers.CharField()
    name = serializers.CharField()
    args = serializers.ListField(child=serializers.JSONField(), required=False)
    children = serializers.ListField(
        child=serializers.CharField(), required=False
    )
    kwargs = serializers.DictField(required=False)
    worker = serializers.CharField(required=False)
    retries = serializers.IntegerField(required=False)
    queue = serializers.CharField(required=False)
    task_id = serializers.CharField()


class TaskIDDataSerializer(serializers.Serializer):
    """serialize task by ID POST data"""

    command = serializers.ChoiceField(choices=["stop", "kill"])


class TaskCreateDataSerializer(serializers.Serializer):
    """serialize task create data"""

    schedule = serializers.CharField(required=False)
    config = serializers.DictField(required=False)


class TaskNotificationItemSerializer(serializers.Serializer):
    """serialize single task notification"""

    urls = serializers.ListField(child=serializers.CharField())
    title = serializers.CharField()


def create_dynamic_notification_serializer():
    """use task config"""
    fields = {
        key: TaskNotificationItemSerializer(required=False)
        for key in TASK_CONFIG
    }
    return type("DynamicDictSerializer", (serializers.Serializer,), fields)


TaskNotificationSerializer = create_dynamic_notification_serializer()


class TaskNotificationPostSerializer(serializers.Serializer):
    """serialize task notification POST"""

    task_name = serializers.ChoiceField(choices=list(TASK_CONFIG))
    url = serializers.CharField(required=False)


class TaskNotificationTestSerializer(serializers.Serializer):
    """serialize task notification test POST"""

    url = serializers.CharField()
    task_name = serializers.ChoiceField(
        choices=list(TASK_CONFIG), required=False
    )
