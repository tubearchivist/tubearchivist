"""
functionality:
- interact with redis
- hold temporary download queue in redis
- interact with celery tasks results
"""

import json

import redis
from home.src.ta.settings import EnvironmentSettings


class RedisBase:
    """connection base for redis"""

    NAME_SPACE: str = EnvironmentSettings.REDIS_NAME_SPACE

    def __init__(self):
        self.conn = redis.Redis(
            host=EnvironmentSettings.REDIS_HOST,
            port=EnvironmentSettings.REDIS_PORT,
            decode_responses=True,
        )


class RedisArchivist(RedisBase):
    """collection of methods to interact with redis"""

    CHANNELS: list[str] = [
        "download",
        "add",
        "rescan",
        "subchannel",
        "subplaylist",
        "playlistscan",
        "setting",
    ]

    def set_message(
        self,
        key: str,
        message: dict,
        path: str = ".",
        expire: bool | int = False,
        save: bool = False,
    ) -> None:
        """write new message to redis"""
        self.conn.execute_command(
            "JSON.SET", self.NAME_SPACE + key, path, json.dumps(message)
        )

        if expire:
            if isinstance(expire, bool):
                secs: int = 20
            else:
                secs = expire
            self.conn.execute_command("EXPIRE", self.NAME_SPACE + key, secs)

        if save:
            self.bg_save()

    def bg_save(self) -> None:
        """save to aof"""
        try:
            self.conn.bgsave()
        except redis.exceptions.ResponseError:
            pass

    def get_message(self, key: str) -> dict:
        """get message dict from redis"""
        reply = self.conn.execute_command("JSON.GET", self.NAME_SPACE + key)
        if reply:
            return json.loads(reply)

        return {"status": False}

    def list_keys(self, query: str) -> list:
        """return all key matches"""
        reply = self.conn.execute_command(
            "KEYS", self.NAME_SPACE + query + "*"
        )
        if not reply:
            return []

        return [i.lstrip(self.NAME_SPACE) for i in reply]

    def list_items(self, query: str) -> list:
        """list all matches"""
        all_matches = self.list_keys(query)
        if not all_matches:
            return []

        return [self.get_message(i) for i in all_matches]

    def del_message(self, key: str) -> bool:
        """delete key from redis"""
        response = self.conn.execute_command("DEL", self.NAME_SPACE + key)
        return response


class RedisQueue(RedisBase):
    """
    dynamically interact with queues in redis using sorted set
    - low score number is first in queue
    - add new items with high score number

    queue names in use:
    download:channel            channels during download
    download:playlist:full      playlists during dl for full refresh
    download:playlist:quick     playlists during dl for quick refresh
    download:video              videos during downloads
    index:comment               videos needing comment indexing
    reindex:ta_video            reindex videos
    reindex:ta_channel          reindex channels
    reindex:ta_playlist         reindex playlists

    """

    def __init__(self, queue_name: str):
        super().__init__()
        self.key = f"{self.NAME_SPACE}{queue_name}"

    def get_all(self) -> list[str]:
        """return all elements in list"""
        result = self.conn.zrange(self.key, 0, -1)
        return result

    def length(self) -> int:
        """return total elements in list"""
        return self.conn.zcard(self.key)

    def in_queue(self, element) -> str | bool:
        """check if element is in list"""
        result = self.conn.zrank(self.key, element)
        if result is not None:
            return "in_queue"

        return False

    def add(self, to_add: str) -> None:
        """add single item to queue"""
        if not to_add:
            return

        next_score = self._get_next_score()
        self.conn.zadd(self.key, {to_add: next_score})

    def add_list(self, to_add: list) -> None:
        """add list to queue"""
        if not to_add:
            return

        next_score = self._get_next_score()
        mapping = {i[1]: next_score + i[0] for i in enumerate(to_add)}
        self.conn.zadd(self.key, mapping)

    def max_score(self) -> int | None:
        """get max score"""
        last = self.conn.zrange(self.key, -1, -1, withscores=True)
        if not last:
            return None

        return int(last[0][1])

    def _get_next_score(self) -> float:
        """get next score in queue to append"""
        last = self.conn.zrange(self.key, -1, -1, withscores=True)
        if not last:
            return 1.0

        return last[0][1] + 1

    def get_next(self) -> tuple[str | None, int | None]:
        """return next element in the queue, if available"""
        result = self.conn.zpopmin(self.key)
        if not result:
            return None, None

        item, idx = result[0][0], int(result[0][1])

        return item, idx

    def clear(self) -> None:
        """delete list from redis"""
        self.conn.delete(self.key)


class TaskRedis(RedisBase):
    """interact with redis tasks"""

    BASE: str = "celery-task-meta-"
    EXPIRE: int = 60 * 60 * 24
    COMMANDS: list[str] = ["STOP", "KILL"]

    def get_all(self) -> list:
        """return all tasks"""
        all_keys = self.conn.execute_command("KEYS", f"{self.BASE}*")
        return [i.replace(self.BASE, "") for i in all_keys]

    def get_single(self, task_id: str) -> dict:
        """return content of single task"""
        result = self.conn.execute_command("GET", self.BASE + task_id)
        if not result:
            return {}

        return json.loads(result)

    def set_key(
        self, task_id: str, message: dict, expire: bool | int = False
    ) -> None:
        """set value for lock, initial or update"""
        key: str = f"{self.BASE}{task_id}"
        self.conn.execute_command("SET", key, json.dumps(message))

        if expire:
            self.conn.execute_command("EXPIRE", key, self.EXPIRE)

    def set_command(self, task_id: str, command: str) -> None:
        """set task command"""
        if command not in self.COMMANDS:
            print(f"{command} not in valid commands {self.COMMANDS}")
            raise ValueError

        message = self.get_single(task_id)
        if not message:
            print(f"{task_id} not found")
            raise KeyError

        message.update({"command": command})
        self.set_key(task_id, message)

    def del_task(self, task_id: str) -> None:
        """delete task result by id"""
        self.conn.execute_command("DEL", f"{self.BASE}{task_id}")

    def del_all(self) -> None:
        """delete all task results"""
        all_tasks = self.get_all()
        for task_id in all_tasks:
            self.del_task(task_id)
