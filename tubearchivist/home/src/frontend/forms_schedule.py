"""
Functionality:
- handle schedule forms
- implement form validation
"""

from celery.schedules import crontab
from django import forms
from home.src.ta.task_config import TASK_CONFIG


class CrontabValidator:
    """validate crontab"""

    @staticmethod
    def validate_fields(cron_fields):
        """expect 3 cron fields"""
        if not len(cron_fields) == 3:
            raise forms.ValidationError("expected three cron schedule fields")

    @staticmethod
    def validate_minute(minute_field):
        """expect minute int"""
        try:
            minute_value = int(minute_field)
            if not 0 <= minute_value <= 59:
                raise forms.ValidationError(
                    "Invalid value for minutes. Must be between 0 and 59."
                )
        except ValueError as err:
            raise forms.ValidationError(
                "Invalid value for minutes. Must be an integer."
            ) from err

    @staticmethod
    def validate_cron_tab(minute, hour, day_of_week):
        """check if crontab can be created"""
        try:
            crontab(minute=minute, hour=hour, day_of_week=day_of_week)
        except ValueError as err:
            raise forms.ValidationError(f"invalid crontab: {err}") from err

    def validate(self, cron_expression):
        """create crontab schedule"""
        if cron_expression == "auto":
            return

        cron_fields = cron_expression.split()
        self.validate_fields(cron_fields)

        minute, hour, day_of_week = cron_fields
        self.validate_minute(minute)
        self.validate_cron_tab(minute, hour, day_of_week)


def validate_cron(cron_expression):
    """callable for field"""
    CrontabValidator().validate(cron_expression)


class SchedulerSettingsForm(forms.Form):
    """handle scheduler settings"""

    update_subscribed = forms.CharField(
        required=False, validators=[validate_cron]
    )
    download_pending = forms.CharField(
        required=False, validators=[validate_cron]
    )
    check_reindex = forms.CharField(required=False, validators=[validate_cron])
    check_reindex_days = forms.IntegerField(required=False)
    thumbnail_check = forms.CharField(
        required=False, validators=[validate_cron]
    )
    run_backup = forms.CharField(required=False, validators=[validate_cron])
    run_backup_rotate = forms.IntegerField(required=False)


class NotificationSettingsForm(forms.Form):
    """add notification URL"""

    SUPPORTED_TASKS = [
        "update_subscribed",
        "extract_download",
        "download_pending",
        "check_reindex",
    ]
    TASK_LIST = [(i, TASK_CONFIG[i]["title"]) for i in SUPPORTED_TASKS]

    TASK_CHOICES = [("", "-- select task --")]
    TASK_CHOICES.extend(TASK_LIST)

    PLACEHOLDER = "Apprise notification URL"

    task = forms.ChoiceField(
        widget=forms.Select, choices=TASK_CHOICES, required=False
    )
    notification_url = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"placeholder": PLACEHOLDER}),
    )
