"""send notifications using apprise"""

import apprise
from django_celery_beat.models import PeriodicTask
from home.src.ta import task_manager  # partial import


class Notifications:
    """notification handler"""

    def __init__(self, name: str, task_id: str, task_title: str):
        self.name: str = name
        self.task_id: str = task_id
        self.task_title: str = task_title

    def send(self) -> None:
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
        try:
            task = PeriodicTask.objects.get(name=self.name)
        except PeriodicTask.DoesNotExist:
            return False

        hooks: str = task.task_config.get("notify")

        return hooks

    def parse_hooks(self, hooks: str) -> list[str]:
        """create list of hooks"""

        hook_list: list[str] = [i.strip() for i in hooks.split()]

        return hook_list

    def build_message(self) -> tuple[str, str | None]:
        """build message to send notification"""
        task = task_manager.TaskManager().get_task(self.task_id)
        status = task.get("status")
        title: str = f"[TA] {self.task_title} process ended with {status}"
        body: str | None = task.get("result")

        return title, body
