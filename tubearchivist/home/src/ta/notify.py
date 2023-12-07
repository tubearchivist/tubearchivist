"""send notifications using apprise"""

import apprise
from home.src.es.connect import ElasticWrap
from home.src.ta import task_manager  # partial import


class Notifications:
    """store notifications in ES"""

    GET_PATH = "ta_config/_doc/notify"
    UPDATE_PATH = "ta_config/_update/notify/"

    def __init__(self, task_name: str):
        self.task_name = task_name

    def send(self, task_id: str, task_title: str) -> None:
        """send notifications"""
        apobj = apprise.Apprise()
        urls: str | None = self.get_urls()
        if not urls:
            return

        title, body = self._build_message(task_id, task_title)

        if not body:
            return

        for url in urls:
            apobj.add(url)

        apobj.notify(body=body, title=title)

    def _build_message(
        self, task_id: str, task_title: str
    ) -> tuple[str, str | None]:
        """build message to send notification"""
        task = task_manager.TaskManager().get_task(task_id)
        status = task.get("status")
        title: str = f"[TA] {task_title} process ended with {status}"
        body: str | None = task.get("result")

        return title, body

    def get_urls(self) -> list[str]:
        """get stored urls for task"""
        response, code = ElasticWrap(self.GET_PATH).get(print_error=False)
        if not code == 200:
            return []

        urls = response["_source"].get(self.task_name, [])

        return urls

    def add_url(self, url: str) -> None:
        """add url to task notification"""
        source = (
            "if (!ctx._source.containsKey(params.task_name)) "
            + "{ctx._source[params.task_name] = [params.url]} "
            + "else if (!ctx._source[params.task_name].contains(params.url)) "
            + "{ctx._source[params.task_name].add(params.url)} "
            + "else {ctx.op = 'none'}"
        )

        data = {
            "script": {
                "source": source,
                "lang": "painless",
                "params": {"url": url, "task_name": self.task_name},
            },
            "upsert": {self.task_name: [url]},
        }

        _, _ = ElasticWrap(self.UPDATE_PATH).post(data)

    def remove_url(self, url: str) -> None:
        """remove url from task"""
        source = (
            "if (ctx._source.containsKey(params.task_name) "
            + "&& ctx._source[params.task_name].contains(params.url)) "
            + "{ctx._source[params.task_name]."
            + "remove(ctx._source[params.task_name].indexOf(params.url))}"
        )

        data = {
            "script": {
                "source": source,
                "lang": "painless",
                "params": {"url": url, "task_name": self.task_name},
            }
        }

        _, _ = ElasticWrap(self.UPDATE_PATH).post(data)

    def remove_task(self) -> None:
        """remove all notifications from task"""
        source = (
            "if (ctx._source.containsKey(params.task_name)) "
            + "{ctx._source.remove(params.task_name)}"
        )
        data = {
            "script": {
                "source": source,
                "lang": "painless",
                "params": {"task_name": self.task_name},
            }
        }

        _, _ = ElasticWrap(self.UPDATE_PATH).post(data)
