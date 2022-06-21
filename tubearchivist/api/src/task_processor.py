"""
Functionality:
- process tasks from API
- validate
- handover to celery
"""

from home.src.ta.ta_redis import RedisArchivist
from home.tasks import download_pending, update_subscribed


class TaskHandler:
    """handle tasks from api"""

    def __init__(self, data):
        self.data = data

    def run_task(self):
        """map data and run"""
        task_name = self.data["run"]
        try:
            to_run = self.exec_map(task_name)
        except KeyError as err:
            print(f"invalid task name {task_name}")
            raise ValueError from err

        response = to_run()
        response.update({"task": task_name})
        return response

    def exec_map(self, task_name):
        """map dict key and return function to execute"""
        exec_map = {
            "download_pending": self._download_pending,
            "rescan_pending": self._rescan_pending,
        }

        return exec_map[task_name]

    @staticmethod
    def _rescan_pending():
        """look for new items in subscribed channels"""
        print("rescan subscribed channels")
        update_subscribed.delay()
        return {"success": True}

    @staticmethod
    def _download_pending():
        """start the download queue"""
        print("download pending")
        running = download_pending.delay()
        print("set task id: " + running.id)
        RedisArchivist().set_message("dl_queue_id", running.id)
        return {"success": True}
