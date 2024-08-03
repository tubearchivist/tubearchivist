"""test schedule parsing"""

# flake8: noqa: E402

import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

import pytest
from task.src.config_schedule import CrontabValidator

INCORRECT_CRONTAB = [
    "0 0 * * *",
    "0 0",
    "0",
]


@pytest.mark.parametrize("invalid_value", INCORRECT_CRONTAB)
def test_invalid_len(invalid_value):
    """raise error on invalid crontab"""
    validator = CrontabValidator()
    with pytest.raises(ValueError, match="three cron schedule fields"):
        validator.validate_cron(invalid_value)


NONE_INT_MINUTE = [
    "* * *",
    "0,30 * *",
    "0,1,2 * *",
    "-1 * *",
]


@pytest.mark.parametrize("invalid_value", NONE_INT_MINUTE)
def test_none_int_crontabs(invalid_value):
    """raise error on invalid crontab"""
    validator = CrontabValidator()
    with pytest.raises(ValueError, match="Must be an integer."):
        validator.validate_cron(invalid_value)


INVALID_MINUTE = ["60 * *", "61 * *"]


@pytest.mark.parametrize("invalid_value", INVALID_MINUTE)
def test_invalid_minute(invalid_value):
    """raise error on invalid crontab"""
    validator = CrontabValidator()
    with pytest.raises(ValueError, match="Must be between 0 and 59."):
        validator.validate_cron(invalid_value)


INVALID_CRONTAB = [
    "0 /1 *",
    "0 0/1 *",
]


@pytest.mark.parametrize("invalid_value", INVALID_CRONTAB)
def test_invalid_crontab(invalid_value):
    """raise error on invalid crontab"""
    validator = CrontabValidator()
    with pytest.raises(ValueError, match="invalid crontab"):
        validator.validate_cron(invalid_value)
