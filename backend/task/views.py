"""all task API views"""

from common.views_base import AdminOnly, ApiBaseView
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from task.models import CustomPeriodicTask
from task.serializers import CustomPeriodicTaskSerializer
from task.src.config_schedule import CrontabValidator, ScheduleBuilder
from task.src.notify import Notifications, get_all_notifications
from task.src.task_config import TASK_CONFIG
from task.src.task_manager import TaskCommand, TaskManager


class TaskListView(ApiBaseView):
    """resolves to /api/task/by-name/
    GET: return a list of all stored task results
    """

    permission_classes = [AdminOnly]

    def get(self, request):
        """handle get request"""
        # pylint: disable=unused-argument
        all_results = TaskManager().get_all_results()

        return Response(all_results)


class TaskNameListView(ApiBaseView):
    """resolves to /api/task/by-name/<task-name>/
    GET: return a list of stored results of task
    POST: start new background process
    """

    permission_classes = [AdminOnly]

    def get(self, request, task_name):
        """handle get request"""
        # pylint: disable=unused-argument
        if task_name not in TASK_CONFIG:
            message = {"message": "invalid task name"}
            return Response(message, status=404)

        all_results = TaskManager().get_tasks_by_name(task_name)

        return Response(all_results)

    def post(self, request, task_name):
        """
        handle post request
        404 for invalid task_name
        400 if task can't be started here without argument
        """
        # pylint: disable=unused-argument
        task_config = TASK_CONFIG.get(task_name)
        if not task_config:
            message = {"message": "invalid task name"}
            return Response(message, status=404)

        if not task_config.get("api_start"):
            message = {"message": "can not start task through this endpoint"}
            return Response(message, status=400)

        message = TaskCommand().start(task_name)

        return Response({"message": message})


class TaskIDView(ApiBaseView):
    """resolves to /api/task/by-id/<task-id>/
    GET: return details of task id
    POST: send command to task by id
    """

    valid_commands = ["stop", "kill"]
    permission_classes = [AdminOnly]

    def get(self, request, task_id):
        """handle get request"""
        # pylint: disable=unused-argument
        task_result = TaskManager().get_task(task_id)
        if not task_result:
            message = {"message": "task id not found"}
            return Response(message, status=404)

        return Response(task_result)

    def post(self, request, task_id):
        """post command to task"""
        command = request.data.get("command")
        if not command or command not in self.valid_commands:
            message = {"message": "no valid command found"}
            return Response(message, status=400)

        task_result = TaskManager().get_task(task_id)
        if not task_result:
            message = {"message": "task id not found"}
            return Response(message, status=404)

        task_conf = TASK_CONFIG.get(task_result.get("name"))
        if command == "stop":
            if not task_conf.get("api_stop"):
                message = {"message": "task can not be stopped"}
                return Response(message, status=400)

            TaskCommand().stop(task_id)
        if command == "kill":
            if not task_conf.get("api_stop"):
                message = {"message": "task can not be killed"}
                return Response(message, status=400)

            TaskCommand().kill(task_id)

        return Response({"message": "command sent"})


class ScheduleListView(ApiBaseView):
    """resolves to /api/task/schedule/
    GET: list all schedules
    """

    permission_classes = [AdminOnly]

    def get(self, request):
        """get all schedules"""
        tasks = CustomPeriodicTask.objects.all()
        response = CustomPeriodicTaskSerializer(tasks, many=True).data
        return Response(response)


class ScheduleView(ApiBaseView):
    """resolves to /api/task/schedule/<task-name>/
    POST: create/update schedule for task with config
    - example: {"schedule": "0 0 *", "config": {"days": 90}}
    DEL: delete schedule for task
    """

    permission_classes = [AdminOnly]

    def get(self, request, task_name):
        """get single schedule by task_name"""
        task = get_object_or_404(CustomPeriodicTask, name=task_name)
        response = CustomPeriodicTaskSerializer(task).data
        return Response(response)

    def post(self, request, task_name):
        """create/update schedule for task"""
        cron_schedule = request.data.get("schedule")
        schedule_config = request.data.get("config")
        if not cron_schedule and not schedule_config:
            message = {"message": "expected schedule or config key"}
            return Response(message, status=400)

        try:
            validator = CrontabValidator()
            validator.validate_cron(cron_schedule)
            validator.validate_config(task_name, schedule_config)
        except ValueError as err:
            return Response({"message": str(err)}, status=400)

        ScheduleBuilder().update_schedule(
            task_name, cron_schedule, schedule_config
        )
        message = f"update schedule for task {task_name}"
        if schedule_config:
            message += f" with config {schedule_config}"

        return Response({"message": message})

    def delete(self, request, task_name):
        """delete schedule by task_name query"""
        task = get_object_or_404(CustomPeriodicTask, name=task_name)
        _ = task.delete()

        return Response({"success": True})


class ScheduleNotification(ApiBaseView):
    """resolves to /api/task/notification/
    GET: get all schedule notifications
    POST: add notification url to task
    DEL: delete notification
    """

    def get(self, request):
        """handle get request"""

        return Response(get_all_notifications())

    def post(self, request):
        """handle create notification"""
        task_name = request.data.get("task_name")
        url = request.data.get("url")

        if not TASK_CONFIG.get(task_name):
            message = {"message": "task_name not found"}
            return Response(message, status=404)

        if not url:
            message = {"message": "missing url key"}
            return Response(message, status=400)

        Notifications(task_name).add_url(url)
        message = {"task_name": task_name, "url": url}

        return Response(message)

    def delete(self, request):
        """handle delete"""

        task_name = request.data.get("task_name")
        url = request.data.get("url")

        if not TASK_CONFIG.get(task_name):
            message = {"message": "task_name not found"}
            return Response(message, status=404)

        if url:
            response, status_code = Notifications(task_name).remove_url(url)
        else:
            response, status_code = Notifications(task_name).remove_task()

        return Response({"response": response, "status_code": status_code})
