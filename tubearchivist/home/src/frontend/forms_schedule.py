"""
Functionality:
- handle schedule forms
- implement form validation
"""

from celery.schedules import crontab
from django import forms


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

    HELP_TEXT = "Add Apprise notification URLs, one per line"

    update_subscribed = forms.CharField(
        required=False, validators=[validate_cron]
    )
    update_subscribed_notify = forms.CharField(
        label=False,
        widget=forms.Textarea(
            attrs={
                "rows": 2,
                "placeholder": HELP_TEXT,
            }
        ),
        required=False,
    )
    download_pending = forms.CharField(
        required=False, validators=[validate_cron]
    )
    download_pending_notify = forms.CharField(
        label=False,
        widget=forms.Textarea(
            attrs={
                "rows": 2,
                "placeholder": HELP_TEXT,
            }
        ),
        required=False,
    )
    check_reindex = forms.CharField(required=False, validators=[validate_cron])
    check_reindex_notify = forms.CharField(
        label=False,
        widget=forms.Textarea(
            attrs={
                "rows": 2,
                "placeholder": HELP_TEXT,
            }
        ),
        required=False,
    )
    check_reindex_days = forms.IntegerField(required=False)
    thumbnail_check = forms.CharField(
        required=False, validators=[validate_cron]
    )
    run_backup = forms.CharField(required=False, validators=[validate_cron])
    run_backup_rotate = forms.IntegerField(required=False)
