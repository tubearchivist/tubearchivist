"""restore config from backup"""

import json
from pathlib import Path

from common.src.env_settings import EnvironmentSettings
from django.core.management.base import BaseCommand
from django_celery_beat.models import CrontabSchedule
from rest_framework.authtoken.models import Token
from task.models import CustomPeriodicTask
from task.src.task_config import TASK_CONFIG
from user.models import Account


class Command(BaseCommand):
    """export"""

    help = "Exports all users and their auth tokens to a JSON file"
    FILE = Path(EnvironmentSettings.CACHE_DIR) / "backup" / "migration.json"

    def handle(self, *args, **options):
        """handle"""
        self.stdout.write("restore users and schedules")
        data = self.get_config()
        self.restore_users(data["user_data"])
        self.restore_schedules(data["schedule_data"])
        self.stdout.write(
            self.style.SUCCESS(
                "    ✓ restore completed. Please restart the container."
            )
        )

    def get_config(self) -> dict:
        """get config from backup"""
        with open(self.FILE, "r", encoding="utf-8") as json_file:
            data = json.loads(json_file.read())

        self.stdout.write(
            self.style.SUCCESS(f"    ✓ json file found: {self.FILE}")
        )

        return data

    def restore_users(self, user_data: list[dict]) -> None:
        """restore users from config"""
        self.stdout.write("delete existing users")
        Account.objects.all().delete()

        self.stdout.write("recreate users")
        for user_info in user_data:
            user = Account.objects.create(
                name=user_info["username"],
                is_staff=user_info["is_staff"],
                is_superuser=user_info["is_superuser"],
                password=user_info["password"],
            )
            for token in user_info["tokens"]:
                Token.objects.create(user=user, key=token)

            self.stdout.write(
                self.style.SUCCESS(
                    f"    ✓ recreated user with name: {user_info['username']}"
                )
            )

    def restore_schedules(self, schedule_data: list[dict]) -> None:
        """restore schedules"""
        self.stdout.write("delete existing schedules")
        CustomPeriodicTask.objects.all().delete()

        self.stdout.write("recreate schedules")
        for schedule in schedule_data:
            task_name = schedule["name"]
            description = TASK_CONFIG[task_name].get("title")
            crontab, _ = CrontabSchedule.objects.get_or_create(
                minute=schedule["crontab"]["minute"],
                hour=schedule["crontab"]["hour"],
                day_of_week=schedule["crontab"]["day_of_week"],
                timezone=EnvironmentSettings.TZ,
            )
            task = CustomPeriodicTask.objects.create(
                name=task_name,
                task=task_name,
                description=description,
                crontab=crontab,
            )
            self.stdout.write(
                self.style.SUCCESS(f"    ✓ recreated schedule: {task}")
            )
