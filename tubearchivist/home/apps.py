"""handle custom startup functions"""

from django.apps import AppConfig


class HomeConfig(AppConfig):
    """call startup funcs"""

    default_auto_field = "django.db.models.BigAutoField"
    name = "home"
