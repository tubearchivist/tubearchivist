"""
Functionality:
- collection of functions and tasks from frontend
- called via user input
"""

from home.src.ta.users import UserConfig
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
        view, setting = self.exec_val.split(":")
        UserConfig(self.current_user).set_value(f"view_style_{view}", setting)
        return {"success": True}

    def _change_grid(self):
        """process change items in grid"""
        grid_items = int(self.exec_val)
        grid_items = max(grid_items, 3)
        grid_items = min(grid_items, 7)
        UserConfig(self.current_user).set_value("grid_items", grid_items)
        return {"success": True}

    def _sort_order(self):
        """change the sort between published to downloaded"""
        if self.exec_val in ["asc", "desc"]:
            UserConfig(self.current_user).set_value(
                "sort_order", self.exec_val
            )
        else:
            UserConfig(self.current_user).set_value("sort_by", self.exec_val)
        return {"success": True}

    def _hide_watched(self):
        """toggle if to show watched vids or not"""
        UserConfig(self.current_user).set_value(
            "hide_watched", bool(int(self.exec_val))
        )
        return {"success": True}

    def _show_subed_only(self):
        """show or hide subscribed channels only on channels page"""
        UserConfig(self.current_user).set_value(
            "show_subed_only", bool(int(self.exec_val))
        )
        return {"success": True}

    def _show_ignored_only(self):
        """switch view on /downloads/ to show ignored only"""
        UserConfig(self.current_user).set_value(
            "show_ignored_only", bool(int(self.exec_val))
        )
        return {"success": True}

    def _db_restore(self):
        """restore es zip from settings page"""
        print("restoring index from backup zip")
        filename = self.exec_val
        run_restore_backup.delay(filename)
        return {"success": True}
