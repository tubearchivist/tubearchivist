"""
functionality:
- interact with in redis stored task results
- handle threads and locks
"""

from home import tasks as ta_tasks
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
        if not tasks:
            return False

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
    """run commands on task"""

    def start(self, task_name):
        """start task by task_name, only pass task that don't take args"""
        task = ta_tasks.app.tasks.get(task_name).delay()
        message = {
            "task_id": task.id,
            "status": task.status,
            "task_name": task.name,
        }

        return message

    def stop(self, task_id):
        """
        send stop signal to task_id,
        needs to be implemented in task to take effect
        """
        handler = TaskRedis()

        task = handler.get_single(task_id)
        if not task["name"] in ta_tasks.BaseTask.TASK_CONFIG:
            raise ValueError

        handler.set_command(task_id, "STOP")

    def kill(self, task_id):
        """send kill signal to task_id"""
        ta_tasks.app.control.revoke(task_id, terminate=True)
