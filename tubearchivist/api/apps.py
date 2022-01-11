"""apps file for api package"""

from django.apps import AppConfig


class ApiConfig(AppConfig):
    """app config"""

    default_auto_field = "django.db.models.BigAutoField"
    name = "api"
