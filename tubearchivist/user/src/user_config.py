"""
Functionality:
- read and write user config backed by ES
- encapsulate persistence of user properties
"""

from typing import TypedDict

from home.src.es.connect import ElasticWrap
from home.src.ta.helper import get_stylesheets


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
    sponsorblock_id: str


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
        sponsorblock_id=None,
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

    def get_value(self, key: str):
        """Get the given key from the users configuration

        Throws a KeyError if the requested Key is not a permitted value"""
        if key not in self._DEFAULT_USER_SETTINGS:
            raise KeyError(f"Unable to read config for unknown key '{key}'")

        return self._config.get(key) or self._DEFAULT_USER_SETTINGS.get(key)

    def set_value(self, key: str, value: str | bool | int):
        """Set or replace a configuration value for the user"""
        self._validate(key, value)
        old = self.get_value(key)
        self._config[key] = value

        # Upsert this property (creating a record if not exists)
        es_payload = {"doc": {"config": {key: value}}, "doc_as_upsert": True}
        es_document_path = f"ta_config/_update/user_{self._user_id}"
        response, status = ElasticWrap(es_document_path).post(es_payload)
        if status < 200 or status > 299:
            raise ValueError(f"Failed storing user value {status}: {response}")

        print(f"User {self._user_id} value '{key}' change: {old} -> {value}")

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
            # this is for a non logged-in user so use all the defaults
            return {}

        # Does this user have configuration stored in ES
        es_document_path = f"ta_config/_doc/user_{self._user_id}"
        response, status = ElasticWrap(es_document_path).get(print_error=False)
        if status == 200 and "_source" in response.keys():
            source = response.get("_source")
            if "config" in source.keys():
                return source.get("config")

        # There is no config in ES
        return {}
