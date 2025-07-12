"""all task API views"""

from common.serializers import (
    AsyncTaskResponseSerializer,
    ErrorResponseSerializer,
)
from common.views_base import AdminOnly, ApiBaseView
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.response import Response
from task.models import CustomPeriodicTask
from task.serializers import (
    CustomPeriodicTaskSerializer,
    TaskCreateDataSerializer,
    TaskIDDataSerializer,
    TaskNotificationPostSerializer,
    TaskNotificationSerializer,
    TaskNotificationTestSerializer,
    TaskResultSerializer,
)
from task.src.config_schedule import CrontabValidator, ScheduleBuilder
from task.src.notify import Notifications, get_all_notifications
from task.src.task_config import TASK_CONFIG
from task.src.task_manager import TaskCommand, TaskManager


class TaskListView(ApiBaseView):
    """resolves to /api/task/by-name/
    GET: return a list of all stored task results
    """

    permission_classes = [AdminOnly]

    @extend_schema(responses=TaskResultSerializer(many=True))
    def get(self, request):
        """get all stored task results"""
        # pylint: disable=unused-argument
        all_results = TaskManager().get_all_results()
        serializer = TaskResultSerializer(all_results, many=True)

        return Response(serializer.data)


class TaskNameListView(ApiBaseView):
    """resolves to /api/task/by-name/<task-name>/
    GET: return a list of stored results of task
    POST: start new background process
    """

    permission_classes = [AdminOnly]

    @extend_schema(
        responses={
            200: OpenApiResponse(TaskResultSerializer(many=True)),
            404: OpenApiResponse(
                ErrorResponseSerializer(), description="task name not found"
            ),
        },
    )
    def get(self, request, task_name):
        """get stored task by name"""
        # pylint: disable=unused-argument
        if task_name not in TASK_CONFIG:
            error = ErrorResponseSerializer({"error": "task name not found"})
            return Response(error.data, status=404)

        all_results = TaskManager().get_tasks_by_name(task_name)
        serializer = TaskResultSerializer(all_results, many=True)

        return Response(serializer.data)

    @extend_schema(
        responses={
            200: OpenApiResponse(AsyncTaskResponseSerializer()),
            400: OpenApiResponse(
                ErrorResponseSerializer(), description="bad request"
            ),
            404: OpenApiResponse(
                ErrorResponseSerializer(), description="task name not found"
            ),
        }
    )
    def post(self, request, task_name):
        """start new task without args"""
        # pylint: disable=unused-argument
        task_config = TASK_CONFIG.get(task_name)
        if not task_config:
            error = ErrorResponseSerializer({"error": "task name not found"})
            return Response(error.data, status=404)

        if not task_config.get("api_start"):
            error = ErrorResponseSerializer(
                {"error": "can not start task through this endpoint"}
            )
            return Response(error.data, status=404)

        message = TaskCommand().start(task_name)
        serializer = AsyncTaskResponseSerializer(message)

        return Response(serializer.data)


class TaskIDView(ApiBaseView):
    """resolves to /api/task/by-id/<task-id>/
    GET: return details of task id
    POST: send command to task by id
    """

    valid_commands = ["stop", "kill"]
    permission_classes = [AdminOnly]

    @extend_schema(
        responses={
            200: OpenApiResponse(TaskResultSerializer()),
            404: OpenApiResponse(
                ErrorResponseSerializer(), description="task not found"
            ),
        },
    )
    def get(self, request, task_id):
        """get task by ID"""
        # pylint: disable=unused-argument
        task_result = TaskManager().get_task(task_id)
        if not task_result:
            error = ErrorResponseSerializer({"error": "task ID not found"})
            return Response(error.data, status=404)

        serializer = TaskResultSerializer(task_result)

        return Response(serializer.data)

    @extend_schema(
        request=TaskIDDataSerializer(),
        responses={
            204: OpenApiResponse(description="task command sent"),
            400: OpenApiResponse(
                ErrorResponseSerializer(), description="bad request"
            ),
            404: OpenApiResponse(
                ErrorResponseSerializer(), description="task not found"
            ),
        },
    )
    def post(self, request, task_id):
        """post command to task"""
        data_serializer = TaskIDDataSerializer(data=request.data)
        data_serializer.is_valid(raise_exception=True)
        validated_data = data_serializer.validated_data

        command = validated_data["command"]

        task_result = TaskManager().get_task(task_id)
        if not task_result:
            error = ErrorResponseSerializer({"error": "task ID not found"})
            return Response(error.data, status=404)

        task_conf = TASK_CONFIG.get(task_result.get("name"))
        if command == "stop":
            if not task_conf.get("api_stop"):
                error = ErrorResponseSerializer(
                    {"error": "task can not be stopped"}
                )
                return Response(error.data, status=400)

            TaskCommand().stop(task_id)
        if command == "kill":
            if not task_conf.get("api_stop"):
                error = ErrorResponseSerializer(
                    {"error": "task can not be killed"}
                )
                return Response(error.data, status=400)

            TaskCommand().kill(task_id)

        return Response(status=204)


class ScheduleListView(ApiBaseView):
    """resolves to /api/task/schedule/
    GET: list all schedules
    """

    permission_classes = [AdminOnly]

    @extend_schema(
        responses={
            200: OpenApiResponse(CustomPeriodicTaskSerializer(many=True)),
        },
    )
    def get(self, request):
        """get all schedules"""
        tasks = CustomPeriodicTask.objects.all()
        serializer = CustomPeriodicTaskSerializer(tasks, many=True)
        return Response(serializer.data)


class ScheduleView(ApiBaseView):
    """resolves to /api/task/schedule/<task-name>/
    POST: create/update schedule for task with config
    - example: {"schedule": "0 0 *", "config": {"days": 90}}
    DEL: delete schedule for task
    """

    permission_classes = [AdminOnly]

    @extend_schema(
        responses={
            200: OpenApiResponse(CustomPeriodicTaskSerializer()),
            404: OpenApiResponse(
                ErrorResponseSerializer(), description="schedule not found"
            ),
        },
    )
    def get(self, request, task_name):
        """get single schedule by task_name"""
        task = get_object_or_404(CustomPeriodicTask, name=task_name)
        serializer = CustomPeriodicTaskSerializer(task)
        return Response(serializer.data)

    @extend_schema(
        request=TaskCreateDataSerializer(),
        responses={
            200: OpenApiResponse(CustomPeriodicTaskSerializer()),
            400: OpenApiResponse(
                ErrorResponseSerializer(), description="bad request"
            ),
        },
    )
    def post(self, request, task_name):
        """create/update schedule for task"""
        data_serializer = TaskCreateDataSerializer(data=request.data)
        data_serializer.is_valid(raise_exception=True)
        validated_data = data_serializer.validated_data

        cron_schedule = validated_data.get("schedule")
        schedule_config = validated_data.get("config")
        if not cron_schedule and not schedule_config:
            error = ErrorResponseSerializer(
                {"error": "expected schedule or config key"}
            )
            return Response(error.data, status=400)

        try:
            validator = CrontabValidator()
            validator.validate_cron(cron_schedule)
            validator.validate_config(task_name, schedule_config)
        except ValueError as err:
            error = ErrorResponseSerializer({"error": str(err)})
            return Response(error.data, status=400)

        task = ScheduleBuilder().update_schedule(
            task_name, cron_schedule, schedule_config
        )
        message = f"update schedule for task {task_name}"
        if schedule_config:
            message += f" with config {schedule_config}"

        print(message)

        serializer = CustomPeriodicTaskSerializer(task)
        return Response(serializer.data)

    @extend_schema(
        responses={
            204: OpenApiResponse(description="schedule deleted"),
            404: OpenApiResponse(
                ErrorResponseSerializer(), description="schedule not found"
            ),
        },
    )
    def delete(self, request, task_name):
        """delete schedule by task_name"""
        task = get_object_or_404(CustomPeriodicTask, name=task_name)
        _ = task.delete()

        return Response(status=204)


class ScheduleNotification(ApiBaseView):
    """resolves to /api/task/notification/
    GET: get all schedule notifications
    POST: add notification url to task
    DEL: delete notification
    """

    @extend_schema(
        responses=TaskNotificationSerializer(),
    )
    def get(self, request):
        """handle get request"""
        serializer = TaskNotificationSerializer(get_all_notifications())

        return Response(serializer.data)

    @extend_schema(
        request=TaskNotificationPostSerializer(),
        responses={
            200: OpenApiResponse(TaskNotificationSerializer()),
            400: OpenApiResponse(
                ErrorResponseSerializer(), description="bad request"
            ),
        },
    )
    def post(self, request):
        """create notification"""
        data_serializer = TaskNotificationPostSerializer(data=request.data)
        data_serializer.is_valid(raise_exception=True)
        validated_data = data_serializer.validated_data

        task_name = validated_data["task_name"]
        url = validated_data["url"]
        if not url:
            error = ErrorResponseSerializer({"error": "missing url"})
            return Response(error.data, status=400)

        Notifications(task_name).add_url(url)

        serializer = TaskNotificationSerializer(get_all_notifications())

        return Response(serializer.data)

    @extend_schema(
        request=TaskNotificationPostSerializer(),
        responses={
            204: OpenApiResponse(description="notification url deleted"),
            400: OpenApiResponse(
                ErrorResponseSerializer(), description="bad request"
            ),
        },
    )
    def delete(self, request):
        """delete notification"""

        data_serializer = TaskNotificationPostSerializer(data=request.data)
        data_serializer.is_valid(raise_exception=True)
        validated_data = data_serializer.validated_data

        task_name = validated_data["task_name"]
        url = validated_data.get("url")

        if url:
            Notifications(task_name).remove_url(url)
        else:
            Notifications(task_name).remove_task()

        return Response(status=204)


class NotificationTestView(ApiBaseView):
    """resolves to /api/task/notification/test/
    POST: test notification url
    """

    @extend_schema(
        request=TaskNotificationTestSerializer(),
        responses={
            200: OpenApiResponse(description="test notification sent"),
            400: OpenApiResponse(
                ErrorResponseSerializer(), description="bad request"
            ),
        },
    )
    def post(self, request):
        """test notification"""
        data_serializer = TaskNotificationTestSerializer(data=request.data)
        data_serializer.is_valid(raise_exception=True)
        validated_data = data_serializer.validated_data

        url = validated_data["url"]
        task_name = validated_data.get("task_name", "manual_test")

        success, message = Notifications(task_name).test(url)

        status = 200 if success else 400
        return Response(
            {"success": success, "message": message}, status=status
        )
