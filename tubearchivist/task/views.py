"""all task API views"""

from api.views import AdminOnly, ApiBaseView
from rest_framework.response import Response
from task.models import CustomPeriodicTask
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

            message_key = self._build_message_key(task_conf, task_id)
            TaskCommand().stop(task_id, message_key)
        if command == "kill":
            if not task_conf.get("api_stop"):
                message = {"message": "task can not be killed"}
                return Response(message, status=400)

            TaskCommand().kill(task_id)

        return Response({"message": "command sent"})

    def _build_message_key(self, task_conf, task_id):
        """build message key to forward command to notification"""
        return f"message:{task_conf.get('group')}:{task_id.split('-')[0]}"


class ScheduleView(ApiBaseView):
    """resolves to /api/task/schedule/<task-name>/
    DEL: delete schedule for task
    """

    permission_classes = [AdminOnly]

    def delete(self, request):
        """delete schedule by task_name query"""
        task_name = request.data.get("task_name")
        try:
            task = CustomPeriodicTask.objects.get(name=task_name)
        except CustomPeriodicTask.DoesNotExist:
            message = {"message": "task_name not found"}
            return Response(message, status=404)

        _ = task.delete()

        return Response({"success": True})


class ScheduleNotification(ApiBaseView):
    """resolves to /api/task/notification/
    GET: get all schedule notifications
    DEL: delete notification
    """

    def get(self, request):
        """handle get request"""

        return Response(get_all_notifications())

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
