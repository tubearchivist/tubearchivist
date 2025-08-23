"""
Functionality:
- read and write user config backed by ES
- encapsulate persistence of user properties
"""

from typing import TypedDict

from common.src.es_connect import ElasticWrap


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
    vid_type_filter: str | None
    grid_items: int
    hide_watched: bool | None
    hide_watched_channel: bool | None
    hide_watched_playlist: bool | None
    file_size_unit: str
    show_ignored_only: bool
    show_subed_only: bool | None
    show_subed_only_playlists: bool | None
    show_help_text: bool


class UserConfig:
    """
    Handle settings for an individual user
    items are expected to be validated in the serializer
    """

    _DEFAULT_USER_SETTINGS = UserConfigType(
        stylesheet="dark.css",
        page_size=12,
        sort_by="published",
        sort_order="desc",
        view_style_home="grid",
        view_style_channel="list",
        view_style_downloads="list",
        view_style_playlist="grid",
        vid_type_filter=None,
        grid_items=3,
        hide_watched=False,
        hide_watched_channel=None,
        hide_watched_playlist=None,
        file_size_unit="binary",
        show_ignored_only=False,
        show_subed_only=None,
        show_subed_only_playlists=None,
        show_help_text=True,
    )

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
        data = {"doc": {"config": {key: value}}}
        response, status = ElasticWrap(self.es_update_url).post(data)
        if status < 200 or status > 299:
            raise ValueError(f"Failed storing user value {status}: {response}")

        print(f"User {self._user_id} value '{key}' change: to {value}")

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

    def update_config(self, to_update: dict) -> None:
        """update config object"""
        data = {"doc": {"config": to_update}}
        response, status = ElasticWrap(self.es_update_url).post(data)
        if status < 200 or status > 299:
            raise ValueError(f"Failed storing user value {status}: {response}")

        for key, value in to_update.items():
            print(f"User {self._user_id} value '{key}' change: to {value}")

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
