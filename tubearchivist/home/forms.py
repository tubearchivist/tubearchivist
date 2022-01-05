"""functionality:
- hold all form classes used in the views
"""

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.forms.widgets import PasswordInput, TextInput


class CustomAuthForm(AuthenticationForm):
    """better styled login form"""

    username = forms.CharField(
        widget=TextInput(
            attrs={
                "placeholder": "Username",
                "autofocus": True,
                "autocomplete": True,
            }
        ),
        label=False,
    )
    password = forms.CharField(
        widget=PasswordInput(attrs={"placeholder": "Password"}), label=False
    )
    remember_me = forms.BooleanField(required=False)


class UserSettingsForm(forms.Form):
    """user configurations values"""

    CHOICES = [
        ("", "-- change color scheme --"),
        ("dark", "Dark"),
        ("light", "Light"),
    ]

    colors = forms.ChoiceField(
        widget=forms.Select, choices=CHOICES, required=False
    )
    page_size = forms.IntegerField(required=False)


class ApplicationSettingsForm(forms.Form):
    """handle all application settings"""

    METADATA_CHOICES = [
        ("", "-- change metadata embed --"),
        ("0", "don't embed metadata"),
        ("1", "embed metadata"),
    ]

    THUMBNAIL_CHOICES = [
        ("", "-- change thumbnail embed --"),
        ("0", "don't embed thumbnail"),
        ("1", "embed thumbnail"),
    ]

    RYD_CHOICES = [
        ("", "-- change ryd integrations"),
        ("0", "disable ryd integration"),
        ("1", "enable ryd integration"),
    ]

    subscriptions_channel_size = forms.IntegerField(required=False)
    downloads_limit_count = forms.IntegerField(required=False)
    downloads_limit_speed = forms.IntegerField(required=False)
    downloads_throttledratelimit = forms.IntegerField(required=False)
    downloads_sleep_interval = forms.IntegerField(required=False)
    downloads_autodelete_days = forms.IntegerField(required=False)
    downloads_format = forms.CharField(required=False)
    downloads_add_metadata = forms.ChoiceField(
        widget=forms.Select, choices=METADATA_CHOICES, required=False
    )
    downloads_add_thumbnail = forms.ChoiceField(
        widget=forms.Select, choices=THUMBNAIL_CHOICES, required=False
    )
    downloads_integrate_ryd = forms.ChoiceField(
        widget=forms.Select, choices=RYD_CHOICES, required=False
    )


class SchedulerSettingsForm(forms.Form):
    """handle scheduler settings"""

    update_subscribed = forms.CharField(required=False)
    download_pending = forms.CharField(required=False)
    check_reindex = forms.CharField(required=False)
    check_reindex_days = forms.IntegerField(required=False)
    thumbnail_check = forms.CharField(required=False)
    run_backup = forms.CharField(required=False)
    run_backup_rotate = forms.IntegerField(required=False)


class MultiSearchForm(forms.Form):
    """multi search form for /search/"""

    searchInput = forms.CharField(
        label="",
        widget=forms.TextInput(
            attrs={
                "autocomplete": "off",
                "oninput": "searchMulti(this.value)",
                "autofocus": True,
            }
        ),
    )


class AddToQueueForm(forms.Form):
    """text area form to add to downloads"""

    vid_url = forms.CharField(
        label=False,
        widget=forms.Textarea(
            attrs={
                "rows": 4,
                "placeholder": "Enter Video Urls or IDs here...",
            }
        ),
    )


class SubscribeToChannelForm(forms.Form):
    """text area form to subscribe to multiple channels"""

    subscribe = forms.CharField(
        label="Subscribe to channels",
        widget=forms.Textarea(
            attrs={
                "rows": 3,
                "placeholder": "Input channel ID, URL or Video of a channel",
            }
        ),
    )


class SubscribeToPlaylistForm(forms.Form):
    """text area form to subscribe to multiple playlists"""

    subscribe = forms.CharField(
        label="Subscribe to playlists",
        widget=forms.Textarea(
            attrs={
                "rows": 3,
                "placeholder": "Input playlist IDs or URLs",
            }
        ),
    )
