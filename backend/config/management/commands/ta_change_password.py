"""change user password"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

User = get_user_model()


class Command(BaseCommand):
    """change password"""

    help = "Change Password of user"

    def add_arguments(self, parser):
        parser.add_argument("username", type=str)
        parser.add_argument("password", type=str)

    def handle(self, *args, **kwargs):
        """entry point"""
        username = kwargs["username"]
        new_password = kwargs["password"]
        self.stdout.write(f"Changing password for user '{username}'")
        try:
            user = User.objects.get(name=username)
        except User.DoesNotExist as err:
            message = f"Username '{username}' does not exist. "
            message += "Available username(s) are:\n"
            message += ", ".join([i.name for i in User.objects.all()])
            raise CommandError(message) from err

        user.set_password(new_password)
        user.save()

        self.stdout.write(
            self.style.SUCCESS(f"    ✓ updated password for user '{username}'")
        )
