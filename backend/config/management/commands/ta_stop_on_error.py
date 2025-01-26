"""stop on unexpected table"""

from time import sleep

from django.core.management.base import BaseCommand, CommandError
from django.db import connection

ERROR_MESSAGE = """
    🗙 Database is incompatible, see latest release notes for instructions:
    🗙 https://github.com/tubearchivist/tubearchivist/releases/tag/v0.5.0
"""


class Command(BaseCommand):
    """command framework"""

    # pylint: disable=no-member

    def handle(self, *args, **options):
        """handle"""
        self.stdout.write("[MIGRATION] Confirming v0.5.0 table layout")
        all_tables = self.list_tables()
        for table in all_tables:
            if table == "home_account":

                self.stdout.write(self.style.ERROR(ERROR_MESSAGE))
                sleep(60)
                raise CommandError(ERROR_MESSAGE)

        self.stdout.write(self.style.SUCCESS("    ✓ local DB is up-to-date."))

    def list_tables(self):
        """raw list all tables"""
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table';"
            )
            tables = cursor.fetchall()

        return [table[0] for table in tables]
