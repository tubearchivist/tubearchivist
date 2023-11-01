"""
Functionality:
- Check environment at startup
- Process config file overwrites from env var
- Stop startup on error
- python management.py ta_envcheck
"""

import os
import re

from django.core.management.base import BaseCommand, CommandError
from home.models import Account
from home.src.ta.settings import EnvironmentSettings

LOGO = """

                         ....  .....
                  ...'',;:cc,. .;::;;,'...
               ..,;:cccllclc,  .:ccllllcc;,..
            ..,:cllcc:;,'.',.  ....'',;ccllc:,..
          ..;cllc:,'..                ...,:cccc:'.
         .;cccc;..                        ..,:ccc:'.
       .ckkkOkxollllllllllllc.      .,:::;.  .,cclc;
      .:0MMMMMMMMMMMMMMMMMMMX:     .cNMMMWx.   .;clc:
     .;lOXK0000KNMMMMX00000KO;     ;KMMMMMNl.   .;ccl:,.
     .;:c:'.....kMMMNo........    'OMMMWMMMK:    '::;;'.
   .......     .xMMMNl           .dWMMXdOMMMO'   ........
   .:cc:;.     .xMMMNc          .lNMMNo.:XMMWx.    .:cl:.
   .:llc,.     .:xxxd,          ;KMMMk. .oWMMNl.   .:llc'
   .cll:.     .;:;;:::,.       'OMMMK:';''kWMMK:   .;llc,
   .cll:.     .,;;;;;;,.     .,xWMMNl.:l:.;KMMMO'  .;llc'
   .:llc.      .cOOOk;      .lKNMMWx..:l:..lNMMWx. .:llc'
   .;lcc,.     .xMMMNc      :KMMMM0, .:lc. .xWMMNl.'ccl:.
    .cllc.     .xMMMNc     'OMMMMXc...:lc...,0MMMKl:lcc,.
    .,ccl:.    .xMMMNc    .xWMMMWo.,;;:lc;;;.cXMMMXdcc;.
     .,clc:.   .xMMMNc   .lNMMMWk. .':clc:,. .dWMMW0o;.
      .,clcc,. .ckkkx;   .okkkOx,    .';,.    'kKKK0l.
       .':lcc:'.....      .  ..            ..,;cllc,.
         .,cclc,....                     ....;clc;..
          ..,:,..,c:'..              ...';:,..,:,.
            ....:lcccc:;,'''.....'',;;:clllc,....
               .'',;:cllllllccccclllllcc:,'..
                   ...'',,;;;;;;;;;,''...
                            .....

"""

TOPIC = """
#######################
#  Environment Setup  #
#######################

"""

EXPECTED_ENV_VARS = [
    "TA_USERNAME",
    "TA_PASSWORD",
    "ELASTIC_PASSWORD",
    "ES_URL",
    "TA_HOST",
]
INST = "https://github.com/tubearchivist/tubearchivist#installing-and-updating"
NGINX = "/etc/nginx/sites-available/default"
UWSGI = "/app/uwsgi.ini"


class Command(BaseCommand):
    """command framework"""

    # pylint: disable=no-member
    help = "Check environment before startup"

    def handle(self, *args, **options):
        """run all commands"""
        self.stdout.write(LOGO)
        self.stdout.write(TOPIC)
        self._expected_vars()
        self._elastic_user_overwrite()
        self._ta_port_overwrite()
        self._ta_uwsgi_overwrite()
        self._enable_cast_overwrite()
        self._create_superuser()

    def _expected_vars(self):
        """check if expected env vars are set"""
        self.stdout.write("[1] checking expected env vars")
        env = os.environ
        for var in EXPECTED_ENV_VARS:
            if not env.get(var):
                message = f"    🗙 expected env var {var} not set\n    {INST}"
                self.stdout.write(self.style.ERROR(message))
                raise CommandError(message)

        message = "    ✓ all expected env vars are set"
        self.stdout.write(self.style.SUCCESS(message))

    def _elastic_user_overwrite(self):
        """check for ELASTIC_USER overwrite"""
        self.stdout.write("[2] check ES user overwrite")
        env = EnvironmentSettings.ES_USER
        self.stdout.write(self.style.SUCCESS(f"    ✓ ES user is set to {env}"))

    def _ta_port_overwrite(self):
        """set TA_PORT overwrite for nginx"""
        self.stdout.write("[3] check TA_PORT overwrite")
        overwrite = EnvironmentSettings.TA_PORT
        if not overwrite:
            self.stdout.write(self.style.SUCCESS("    TA_PORT is not set"))
            return

        regex = re.compile(r"listen [0-9]{1,5}")
        to_overwrite = f"listen {overwrite}"
        changed = file_overwrite(NGINX, regex, to_overwrite)
        if changed:
            message = f"    ✓ TA_PORT changed to {overwrite}"
        else:
            message = f"    ✓ TA_PORT already set to {overwrite}"

        self.stdout.write(self.style.SUCCESS(message))

    def _ta_uwsgi_overwrite(self):
        """set TA_UWSGI_PORT overwrite"""
        self.stdout.write("[4] check TA_UWSGI_PORT overwrite")
        overwrite = EnvironmentSettings.TA_UWSGI_PORT
        if not overwrite:
            message = "    TA_UWSGI_PORT is not set"
            self.stdout.write(self.style.SUCCESS(message))
            return

        # nginx
        regex = re.compile(r"uwsgi_pass localhost:[0-9]{1,5}")
        to_overwrite = f"uwsgi_pass localhost:{overwrite}"
        changed = file_overwrite(NGINX, regex, to_overwrite)

        # uwsgi
        regex = re.compile(r"socket = :[0-9]{1,5}")
        to_overwrite = f"socket = :{overwrite}"
        changed = file_overwrite(UWSGI, regex, to_overwrite)

        if changed:
            message = f"    ✓ TA_UWSGI_PORT changed to {overwrite}"
        else:
            message = f"    ✓ TA_UWSGI_PORT already set to {overwrite}"

        self.stdout.write(self.style.SUCCESS(message))

    def _enable_cast_overwrite(self):
        """cast workaround, remove auth for static files in nginx"""
        self.stdout.write("[5] check ENABLE_CAST overwrite")
        overwrite = EnvironmentSettings.ENABLE_CAST
        if not overwrite:
            self.stdout.write(self.style.SUCCESS("    ENABLE_CAST is not set"))
            return

        regex = re.compile(r"[^\S\r\n]*auth_request /api/ping/;\n")
        changed = file_overwrite(NGINX, regex, "")
        if changed:
            message = "    ✓ process nginx to enable Cast"
        else:
            message = "    ✓ Cast is already enabled in nginx"

        self.stdout.write(self.style.SUCCESS(message))

    def _create_superuser(self):
        """create superuser if not exist"""
        self.stdout.write("[6] create superuser")
        is_created = Account.objects.filter(is_superuser=True)
        if is_created:
            message = "    superuser already created"
            self.stdout.write(self.style.SUCCESS(message))
            return

        name = EnvironmentSettings.TA_USERNAME
        password = EnvironmentSettings.TA_PASSWORD
        Account.objects.create_superuser(name, password)
        message = f"    ✓ new superuser with name {name} created"
        self.stdout.write(self.style.SUCCESS(message))


def file_overwrite(file_path, regex, overwrite):
    """change file content from old to overwrite, return true when changed"""
    with open(file_path, "r", encoding="utf-8") as f:
        file_content = f.read()

    changed = re.sub(regex, overwrite, file_content)
    if changed == file_content:
        return False

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(changed)

    return True
