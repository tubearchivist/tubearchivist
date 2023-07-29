"""send notifications using apprise"""

import apprise
from home.src.ta.config import AppConfig
from home.src.ta.task_manager import TaskManager


class Notifications:
    """notification handler"""

    def __init__(self, name, task_id, task_title):
        self.name = name
        self.task_id = task_id
        self.task_title = task_title

    def send(self):
        """send notifications"""
        apobj = apprise.Apprise()
        hooks: str | None = self.get_url()
        if not hooks:
            return

        hook_list: list[str] = self.parse_hooks(hooks=hooks)
        title, body = self.build_message()

        if not body:
            return

        for hook in hook_list:
            apobj.add(hook)

        apobj.notify(body=body, title=title)

    def get_url(self) -> str | None:
        """get apprise urls for task"""
        config = AppConfig().config
        hooks: str = config["scheduler"].get(f"{self.name}_notify")

        return hooks

    def parse_hooks(self, hooks: str) -> list[str]:
        """create list of hooks"""

        hook_list: list[str] = [i.strip() for i in hooks.split()]

        return hook_list

    def build_message(self) -> tuple[str, str | None]:
        """build message to send notification"""
        task = TaskManager().get_task(self.task_id)
        status = task.get("status")
        title: str = f"[TA] {self.task_title} process ended with {status}"
        body: str | None = task.get("result")

        return title, body
