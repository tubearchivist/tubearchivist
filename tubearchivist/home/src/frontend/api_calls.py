"""
Functionality:
- collection of functions and tasks from frontend
- called via user input
"""

from home.src.ta.ta_redis import RedisArchivist
from home.tasks import run_restore_backup


class PostData:
    """
    map frontend http post values to backend funcs
    handover long running tasks to celery
    """

    def __init__(self, post_dict, current_user):
        self.post_dict = post_dict
        self.to_exec, self.exec_val = list(post_dict.items())[0]
        self.current_user = current_user

    def run_task(self):
        """execute and return task result"""
        to_exec = self.exec_map()
        task_result = to_exec()
        return task_result

    def exec_map(self):
        """map dict key and return function to execute"""
        exec_map = {
            "change_view": self._change_view,
            "change_grid": self._change_grid,
            "sort_order": self._sort_order,
            "hide_watched": self._hide_watched,
            "show_subed_only": self._show_subed_only,
            "show_ignored_only": self._show_ignored_only,
            "db-restore": self._db_restore,
        }

        return exec_map[self.to_exec]

    def _change_view(self):
        """process view changes in home, channel, and downloads"""
        origin, new_view = self.exec_val.split(":")
        key = f"{self.current_user}:view:{origin}"
        print(f"change view: {key} to {new_view}")
        RedisArchivist().set_message(key, {"status": new_view})
        return {"success": True}

    def _change_grid(self):
        """process change items in grid"""
        grid_items = int(self.exec_val)
        grid_items = max(grid_items, 3)
        grid_items = min(grid_items, 7)

        key = f"{self.current_user}:grid_items"
        print(f"change grid items: {grid_items}")
        RedisArchivist().set_message(key, {"status": grid_items})
        return {"success": True}

    def _sort_order(self):
        """change the sort between published to downloaded"""
        sort_order = {"status": self.exec_val}
        if self.exec_val in ["asc", "desc"]:
            RedisArchivist().set_message(
                f"{self.current_user}:sort_order", sort_order
            )
        else:
            RedisArchivist().set_message(
                f"{self.current_user}:sort_by", sort_order
            )
        return {"success": True}

    def _hide_watched(self):
        """toggle if to show watched vids or not"""
        key = f"{self.current_user}:hide_watched"
        message = {"status": bool(int(self.exec_val))}
        print(f"toggle {key}: {message}")
        RedisArchivist().set_message(key, message)
        return {"success": True}

    def _show_subed_only(self):
        """show or hide subscribed channels only on channels page"""
        key = f"{self.current_user}:show_subed_only"
        message = {"status": bool(int(self.exec_val))}
        print(f"toggle {key}: {message}")
        RedisArchivist().set_message(key, message)
        return {"success": True}

    def _show_ignored_only(self):
        """switch view on /downloads/ to show ignored only"""
        show_value = self.exec_val
        key = f"{self.current_user}:show_ignored_only"
        value = {"status": show_value}
        print(f"Filter download view ignored only: {show_value}")
        RedisArchivist().set_message(key, value)
        return {"success": True}

    def _db_restore(self):
        """restore es zip from settings page"""
        print("restoring index from backup zip")
        filename = self.exec_val
        run_restore_backup.delay(filename)
        return {"success": True}
