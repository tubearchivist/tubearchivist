"""functionality:
- hold all form classes used in the views
"""

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.forms.widgets import PasswordInput, TextInput


class CustomAuthForm(AuthenticationForm):
    """better styled login form"""

    username = forms.CharField(
        widget=TextInput(attrs={"placeholder": "Username"}), label=False
    )
    password = forms.CharField(
        widget=PasswordInput(attrs={"placeholder": "Password"}), label=False
    )


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

    subscriptions_channel_size = forms.IntegerField(required=False)
    downloads_limit_count = forms.IntegerField(required=False)
    downloads_limit_speed = forms.IntegerField(required=False)
    downloads_throttledratelimit = forms.IntegerField(required=False)
    downloads_sleep_interval = forms.IntegerField(required=False)
    downloads_format = forms.CharField(required=False)
    downloads_add_metadata = forms.ChoiceField(
        widget=forms.Select, choices=METADATA_CHOICES, required=False
    )
    downloads_add_thumbnail = forms.ChoiceField(
        widget=forms.Select, choices=THUMBNAIL_CHOICES, required=False
    )


class VideoSearchForm(forms.Form):
    """search videos form"""

    searchInput = forms.CharField(
        label="Search your videos",
        widget=forms.TextInput(attrs={"autocomplete": "off"}),
    )


class ChannelSearchForm(forms.Form):
    """search for channels"""

    searchInput = forms.CharField(
        label="",
        widget=forms.TextInput(
            attrs={
                "oninput": "searchChannels(this.value)",
                "autocomplete": "off",
                "list": "resultBox",
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
        label=False,
        widget=forms.Textarea(
            attrs={
                "rows": 3,
                "placeholder": "Input channel ID, URL or Video of a channel",
            }
        ),
    )
