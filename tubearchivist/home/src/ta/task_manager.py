"""
functionality:
- interact with in redis stored task results
- handle threads and locks
"""

from home.src.ta.ta_redis import TaskRedis


class TaskManager:
    """manage tasks"""

    def get_all_results(self):
        """return all task results"""
        handler = TaskRedis()
        all_keys = handler.get_all()
        if not all_keys:
            return False

        return [handler.get_single(i) for i in all_keys]

    def get_tasks_by_name(self, task_name):
        """get all tasks by name"""
        all_results = self.get_all_results()
        if not all_results:
            return False

        return [i for i in all_results if i.get("name") == task_name]

    def get_task(self, task_id):
        """get single task"""
        return TaskRedis().get_single(task_id)

    def is_pending(self, task):
        """check if task_name is pending, pass task object"""
        tasks = self.get_tasks_by_name(task.name)
        return bool([i for i in tasks if i.get("status") == "PENDING"])

    def get_pending(self, task_name):
        """get all pending tasks of task_name"""
        tasks = self.get_tasks_by_name(task_name)
        if not tasks:
            return False

        return [i for i in tasks if i.get("status") == "PENDING"]

    def init(self, task):
        """pass task object from bind task to set initial pending message"""
        message = {
            "status": "PENDING",
            "result": None,
            "traceback": None,
            "date_done": False,
            "name": task.name,
            "task_id": task.request.id,
        }
        TaskRedis().set_key(task.request.id, message)


class TaskCommand:
    """send command pending task"""

    def __init__(self, command="STOP"):
        self.command = command

    def by_id(self, task_id):
        """run command on single task id"""
        self._set_command(task_id)

    def by_name(self, task_name):
        """run command on all tasks by name"""
        pending = TaskManager().get_pending(task_name)
        if not pending:
            return

        for task in pending:
            self._set_command(task.get("task_id"))

    def _set_command(self, task_id):
        """stop single task by id"""
        TaskRedis().set_command(task_id, self.command)
        if self.command == "KILL":
            self._kill(task_id)

    def _kill(self, task_id):
        """kill task by id"""
        from home.tasks import app as CeleryApp

        CeleryApp.control.revoke(task_id, terminate=True)
