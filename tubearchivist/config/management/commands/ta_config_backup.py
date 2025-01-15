"""backup config for sqlite reset and restore"""

import json
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from home.models import CustomPeriodicTask
from home.src.ta.settings import EnvironmentSettings
from rest_framework.authtoken.models import Token

User = get_user_model()


class Command(BaseCommand):
    """export"""

    help = "Exports all users and their auth tokens to a JSON file"
    FILE = Path(EnvironmentSettings.CACHE_DIR) / "backup" / "migration.json"

    def handle(self, *args, **kwargs):
        """entry point"""

        data = {
            "user_data": self.get_users(),
            "schedule_data": self.get_schedules(),
        }

        with open(self.FILE, "w", encoding="utf-8") as json_file:
            json_file.write(json.dumps(data))

    def get_users(self):
        """get users"""

        users = User.objects.all()

        user_data = []

        for user in users:
            user_info = {
                "username": user.name,
                "is_staff": user.is_staff,
                "is_superuser": user.is_superuser,
                "password": user.password,
                "tokens": [],
            }

            try:
                token = Token.objects.get(user=user)
                user_info["tokens"] = [token.key]
            except Token.DoesNotExist:
                user_info["tokens"] = []

            user_data.append(user_info)

        return user_data

    def get_schedules(self):
        """get schedules"""

        all_schedules = CustomPeriodicTask.objects.all()
        schedule_data = []

        for schedule in all_schedules:
            schedule_info = {
                "name": schedule.name,
                "crontab": {
                    "minute": schedule.crontab.minute,
                    "hour": schedule.crontab.hour,
                    "day_of_week": schedule.crontab.day_of_week,
                },
            }

            schedule_data.append(schedule_info)

        return schedule_data
