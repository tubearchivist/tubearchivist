"""
Functionality:
- check that all connections are working
"""

import sys
from time import sleep

import requests
from django.core.management.base import BaseCommand, CommandError
from home.src.es.connect import ElasticWrap


TOPIC = """

#######################
#  Connection check   #
#######################

"""

class Command(BaseCommand):
    """command framework"""

    TIMEOUT = 120

    # pylint: disable=no-member
    help = "Check connections"

    def handle(self, *args, **options):
        """run all commands"""
        self.stdout.write(TOPIC)
        self._es_connection_check()

    def _es_connection_check(self):
        """wait for elasticsearch connection"""
        self.stdout.write("[1] connect to Elastic Search")
        sys.stdout.write("    .")
        for _ in range(self.TIMEOUT // 5):
            sleep(2)
            sys.stdout.write(".")
            try:
                response, status_code = ElasticWrap("/").get(
                    timeout=1, print_error=False
                )
            except requests.exceptions.ConnectionError:
                pass

            if status_code == 200:
                self.stdout.write("\n    ✓ ES connection established")
                return

        message = "    🗙 ES connection failed"
        self.stdout.write(self.style.ERROR(f"\n{message}"))
        self.stdout.write(f"    error message: {response | None}")
        self.stdout.write(f"    status code: {status_code | None}")
        raise CommandError(message)
