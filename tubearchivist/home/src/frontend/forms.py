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

    SP_CHOICES = [
        ("", "-- change sponsorblock integrations"),
        ("0", "disable sponsorblock integration"),
        ("1", "enable sponsorblock integration"),
    ]

    CAST_CHOICES = [
        ("", "-- change Cast integration --"),
        ("0", "disable Cast"),
        ("1", "enable Cast"),
    ]

    SUBTITLE_SOURCE_CHOICES = [
        ("", "-- change subtitle source settings"),
        ("user", "only download user created"),
        ("auto", "also download auto generated"),
    ]

    SUBTITLE_INDEX_CHOICES = [
        ("", "-- change subtitle index settings --"),
        ("0", "disable subtitle index"),
        ("1", "enable subtitle index"),
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
    downloads_subtitle = forms.CharField(required=False)
    downloads_subtitle_source = forms.ChoiceField(
        widget=forms.Select, choices=SUBTITLE_SOURCE_CHOICES, required=False
    )
    downloads_subtitle_index = forms.ChoiceField(
        widget=forms.Select, choices=SUBTITLE_INDEX_CHOICES, required=False
    )
    downloads_integrate_ryd = forms.ChoiceField(
        widget=forms.Select, choices=RYD_CHOICES, required=False
    )
    downloads_integrate_sponsorblock = forms.ChoiceField(
        widget=forms.Select, choices=SP_CHOICES, required=False
    )
    application_enable_cast = forms.ChoiceField(
        widget=forms.Select, choices=CAST_CHOICES, required=False
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
    home = forms.CharField(widget=forms.HiddenInput())
    channel = forms.CharField(widget=forms.HiddenInput())
    playlist = forms.CharField(widget=forms.HiddenInput())


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


class ChannelOverwriteForm(forms.Form):
    """custom overwrites for channel settings"""

    PLAYLIST_INDEX = [
        ("", "-- change playlist index --"),
        ("0", "Disable playlist index"),
        ("1", "Enable playlist index"),
    ]

    SP_CHOICES = [
        ("", "-- change sponsorblock integrations"),
        ("0", "disable sponsorblock integration"),
        ("1", "enable sponsorblock integration"),
    ]

    download_format = forms.CharField(label=False, required=False)
    autodelete_days = forms.IntegerField(label=False, required=False)
    index_playlists = forms.ChoiceField(
        widget=forms.Select, choices=PLAYLIST_INDEX, required=False
    )
    integrate_sponsorblock = forms.ChoiceField(
        widget=forms.Select, choices=SP_CHOICES, required=False
    )
