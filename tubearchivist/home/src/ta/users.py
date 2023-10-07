"""
Functionality:
- read and write user config backed by ES
- encapsulate persistence of user properties
"""

from typing import TypedDict

from home.src.es.connect import ElasticWrap


class UserConfigType(TypedDict, total=False):
    """describes the user configuration"""

    colors: str
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
    """Handle settings for an individual user

    Create getters and setters for usage in the application.
    Although tedious it helps prevents everything caring about how properties
    are persisted. Plus it allows us to save anytime any value is set.
    """

    _DEFAULT_USER_SETTINGS = UserConfigType(
        colors="dark",
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

    def __init__(self, user_id: str):
        self._user_id: str = user_id
        self._config: UserConfigType = self._get_config()

    def get_value(self, key: str):
        """Get the given key from the users configuration

        Throws a KeyError if the requested Key is not a permitted value"""
        if key not in self._DEFAULT_USER_SETTINGS:
            raise KeyError(f"Unable to read config for unknown key '{key}'")

        return self._config.get(key) or self._DEFAULT_USER_SETTINGS.get(key)

    def set_value(self, key: str, value: str | bool | int):
        """Set or replace a configuration value for the user

        Throws a KeyError if the requested Key is not a permitted value"""
        if not self._user_id:
            raise ValueError("Unable to persist config for null user_id")

        if key not in self._DEFAULT_USER_SETTINGS:
            raise KeyError(f"Unable to persist config for unknown key '{key}'")

        old = self.get_value(key)
        self._config[key] = value

        # Upsert this property (creating a record if not exists)
        es_payload = {"doc": {"config": {key: value}}, "doc_as_upsert": True}
        es_document_path = f"ta_config/_update/user_{self._user_id}"
        response, status = ElasticWrap(es_document_path).post(es_payload)
        if status < 200 or status > 299:
            raise ValueError(f"Failed storing user value {status}: {response}")

        print(f"User {self._user_id} value '{key}' change: {old} > {value}")

    def _get_config(self) -> UserConfigType:
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
