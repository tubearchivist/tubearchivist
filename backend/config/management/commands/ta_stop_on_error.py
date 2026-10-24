"""stop on pending v0.6.0 environment migration"""

import os
from time import sleep

from django.core.management.base import BaseCommand, CommandError

REMOVED_ENV_VARS = ("HOST_UID", "HOST_GID", "TA_BACKEND_PORT")

ERROR_MESSAGE = """
    🗙 Startup blocked: environment variables removed in v0.6.0 are set:
    🗙 {variables}
    🗙 Remove these variables from your container configuration.
    🗙 For HOST_UID/HOST_GID, configure the container user and file ownership.
    🗙 For TA_BACKEND_PORT, use TA_PORT instead if overriding the port.
    🗙 Follow the v0.6.0 migration guide before restarting:
    🗙 https://github.com/tubearchivist/tubearchivist/releases/tag/v0.6.0
"""


class Command(BaseCommand):
    """command framework"""

    # pylint: disable=no-member

    def handle(self, *args, **options):
        """require removal of obsolete environment variables"""
        self.stdout.write("[MIGRATION] Confirming v0.6.0 environment")
        variables = [var for var in REMOVED_ENV_VARS if var in os.environ]
        if variables:
            message = ERROR_MESSAGE.format(variables=", ".join(variables))
            self.stdout.write(self.style.ERROR(message))
            sleep(60)
            raise CommandError(message)

        self.stdout.write(
            self.style.SUCCESS("    ✓ environment is up-to-date.")
        )
