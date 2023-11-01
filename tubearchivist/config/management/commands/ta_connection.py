"""
Functionality:
- check that all connections are working
"""

from time import sleep

import requests
from django.core.management.base import BaseCommand, CommandError
from home.src.es.connect import ElasticWrap
from home.src.ta.settings import EnvironmentSettings
from home.src.ta.ta_redis import RedisArchivist

TOPIC = """

#######################
#  Connection check   #
#######################

"""


class Command(BaseCommand):
    """command framework"""

    TIMEOUT = 120
    MIN_MAJOR, MAX_MAJOR = 8, 8
    MIN_MINOR = 0

    # pylint: disable=no-member
    help = "Check connections"

    def handle(self, *args, **options):
        """run all commands"""
        self.stdout.write(TOPIC)
        self._redis_connection_check()
        self._redis_config_set()
        self._es_connection_check()
        self._es_version_check()
        self._es_path_check()

    def _redis_connection_check(self):
        """check ir redis connection is established"""
        self.stdout.write("[1] connect to Redis")
        redis_conn = RedisArchivist().conn
        for _ in range(5):
            try:
                pong = redis_conn.execute_command("PING")
                if pong:
                    self.stdout.write(
                        self.style.SUCCESS("    ✓ Redis connection verified")
                    )
                    return

            except Exception:  # pylint: disable=broad-except
                self.stdout.write("    ... retry Redis connection")
                sleep(2)

        message = "    🗙 Redis connection failed"
        self.stdout.write(self.style.ERROR(f"{message}"))
        RedisArchivist().exec("PING")
        sleep(60)
        raise CommandError(message)

    def _redis_config_set(self):
        """set config for redis if not set already"""
        self.stdout.write("[2] set Redis config")
        redis_conn = RedisArchivist().conn
        timeout_is = int(redis_conn.config_get("timeout").get("timeout"))
        if not timeout_is:
            redis_conn.config_set("timeout", 3600)

        self.stdout.write(self.style.SUCCESS("    ✓ Redis config set"))

    def _es_connection_check(self):
        """wait for elasticsearch connection"""
        self.stdout.write("[3] connect to Elastic Search")
        total = self.TIMEOUT // 5
        for i in range(total):
            self.stdout.write(f"    ... waiting for ES [{i}/{total}]")
            try:
                _, status_code = ElasticWrap("/").get(
                    timeout=1, print_error=False
                )
            except (
                requests.exceptions.ConnectionError,
                requests.exceptions.Timeout,
            ):
                sleep(5)
                continue

            if status_code and status_code == 200:
                path = "_cluster/health?wait_for_status=yellow&timeout=60s"
                _, _ = ElasticWrap(path).get(timeout=60)
                self.stdout.write(
                    self.style.SUCCESS("    ✓ ES connection established")
                )
                return

        response, status_code = ElasticWrap("/").get(
            timeout=1, print_error=False
        )

        message = "    🗙 ES connection failed"
        self.stdout.write(self.style.ERROR(f"{message}"))
        self.stdout.write(f"    error message: {response}")
        self.stdout.write(f"    status code: {status_code}")
        sleep(60)
        raise CommandError(message)

    def _es_version_check(self):
        """check for minimal elasticsearch version"""
        self.stdout.write("[4] Elastic Search version check")
        response, _ = ElasticWrap("/").get()
        version = response["version"]["number"]
        major = int(version.split(".")[0])

        if self.MIN_MAJOR <= major <= self.MAX_MAJOR:
            self.stdout.write(
                self.style.SUCCESS("    ✓ ES version check passed")
            )
            return

        message = (
            "    🗙 ES version check failed. "
            + f"Expected {self.MIN_MAJOR}.{self.MIN_MINOR} but got {version}"
        )
        self.stdout.write(self.style.ERROR(f"{message}"))
        sleep(60)
        raise CommandError(message)

    def _es_path_check(self):
        """check that path.repo var is set"""
        self.stdout.write("[5] check ES path.repo env var")
        response, _ = ElasticWrap("_nodes/_all/settings").get()
        snaphost_roles = [
            "data",
            "data_cold",
            "data_content",
            "data_frozen",
            "data_hot",
            "data_warm",
            "master",
        ]
        for node in response["nodes"].values():
            if not (set(node["roles"]) & set(snaphost_roles)):
                continue

            if node["settings"]["path"].get("repo"):
                self.stdout.write(
                    self.style.SUCCESS("    ✓ path.repo env var is set")
                )
                return

            message = (
                "    🗙 path.repo env var not found. "
                + "set the following env var to the ES container:\n"
                + "    path.repo="
                + EnvironmentSettings.ES_SNAPSHOT_DIR
            )
            self.stdout.write(self.style.ERROR(message))
            sleep(60)
            raise CommandError(message)
