"""
Functionality:
- read and write user config backed by ES
- encapsulate persistence of user properties
"""

from typing import TypedDict

from common.src.es_connect import ElasticWrap
from common.src.helper import get_stylesheets


class UserConfigType(TypedDict, total=False):
    """describes the user configuration"""

    stylesheet: str
    page_size: int
    sort_by: str
    sort_order: str
    view_style_home: str
    view_style_channel: str
    view_style_downloads: str
    view_style_playlist: str
    grid_items: int
    hide_watched: bool
    show_ignored_only: bool
    show_subed_only: bool
    show_help_text: bool


class UserConfig:
    """Handle settings for an individual user"""

    _DEFAULT_USER_SETTINGS = UserConfigType(
        stylesheet="dark.css",
        page_size=12,
        sort_by="published",
        sort_order="desc",
        view_style_home="grid",
        view_style_channel="list",
        view_style_downloads="list",
        view_style_playlist="grid",
        grid_items=3,
        hide_watched=False,
        show_ignored_only=False,
        show_subed_only=False,
        show_help_text=True,
    )

    VALID_STYLESHEETS = get_stylesheets()
    VALID_VIEW_STYLE = ["grid", "list"]
    VALID_SORT_ORDER = ["asc", "desc"]
    VALID_SORT_BY = [
        "published",
        "downloaded",
        "views",
        "likes",
        "duration",
        "filesize",
    ]
    VALID_GRID_ITEMS = range(3, 8)

    def __init__(self, user_id: str):
        self._user_id: str = user_id
        self._config: UserConfigType = self.get_config()

    @property
    def es_url(self) -> str:
        """es URL"""
        return f"ta_config/_doc/user_{self._user_id}"

    @property
    def es_update_url(self) -> str:
        """es update URL"""
        return f"ta_config/_update/user_{self._user_id}"

    def get_value(self, key: str):
        """Get the given key from the users configuration
        Throws a KeyError if the requested Key is not a permitted value"""
        if key not in self._DEFAULT_USER_SETTINGS:
            raise KeyError(f"Unable to read config for unknown key '{key}'")

        return self._config.get(key)

    def set_value(self, key: str, value: str | bool | int):
        """Set or replace a configuration value for the user"""
        self._validate(key, value)
        data = {"doc": {"config": {key: value}}}
        response, status = ElasticWrap(self.es_update_url).post(data)
        if status < 200 or status > 299:
            raise ValueError(f"Failed storing user value {status}: {response}")

        print(f"User {self._user_id} value '{key}' change: to {value}")

    def _validate(self, key, value):
        """validate key and value"""
        if not self._user_id:
            raise ValueError("Unable to persist config for null user_id")

        if key not in self._DEFAULT_USER_SETTINGS:
            raise KeyError(
                f"Unable to persist config for an unknown key '{key}'"
            )

        valid_values = {
            "stylesheet": self.VALID_STYLESHEETS,
            "sort_by": self.VALID_SORT_BY,
            "sort_order": self.VALID_SORT_ORDER,
            "view_style_home": self.VALID_VIEW_STYLE,
            "view_style_channel": self.VALID_VIEW_STYLE,
            "view_style_download": self.VALID_VIEW_STYLE,
            "view_style_playlist": self.VALID_VIEW_STYLE,
            "grid_items": self.VALID_GRID_ITEMS,
            "page_size": int,
            "hide_watched": bool,
            "show_ignored_only": bool,
            "show_subed_only": bool,
            "show_help_text": bool,
        }
        validation_value = valid_values.get(key)

        if isinstance(validation_value, (list, range)):
            if value not in validation_value:
                raise ValueError(f"Invalid value for {key}: {value}")
        elif validation_value == int:
            if not isinstance(value, int):
                raise ValueError(f"Invalid value for {key}: {value}")
        elif validation_value == bool:
            if not isinstance(value, bool):
                raise ValueError(f"Invalid value for {key}: {value}")

    def get_config(self) -> UserConfigType:
        """get config from ES or load from the application defaults"""
        if not self._user_id:
            raise ValueError("no user_id passed")

        response, status = ElasticWrap(self.es_url).get(print_error=False)
        if status == 404:
            self.sync_defaults()
            config = self._DEFAULT_USER_SETTINGS
        else:
            config = self.sync_new_defaults(response["_source"]["config"])

        return config

    def sync_defaults(self):
        """set initial defaults on 404"""
        response, _ = ElasticWrap(self.es_url).post(
            {"config": self._DEFAULT_USER_SETTINGS}
        )
        print(f"set default config for user {self._user_id}: {response}")

    def sync_new_defaults(self, config):
        """sync new defaults"""
        for key, value in self._DEFAULT_USER_SETTINGS.items():
            if key not in config:
                self.set_value(key, value)
                config.update({key: value})

        return config
