"""
Functionality:
- read and write user config backed by ES
- encapsulate persistence of user properties
"""

from home.src.es.connect import ElasticWrap
from home.src.ta.helper import randomizor


class UserConfig:
    """Handle settings for an individual user

    Create getters and setters for usage in the application.
    Although tedious it helps prevents everything caring about how properties
    are persisted. Plus it allows us to save anytime any property is set.
    """

    _DEFAULT_USER_SETTINGS = {
        "colors": "dark",
        "page_size": 12,
        "sort_by": "published",
        "sort_order": "desc",
        "view_style_home": "grid",
        "view_style_channel": "list",
        "view_style_downloads": "list",
        "view_style_playlist": "grid",
        "grid_items": 3,
        "hide_watched": False,
        "show_ignored_only": False,
        "show_subed_only": False,
        "sponsorblock_id": None,
    }

    def __init__(self, user_id: str):
        self._user_id: str = user_id
        self._document_path: str = f"ta_config/_doc/user_{user_id}"
        self._config: dict[str, any] = self._get_config()

    def get_colors(self) -> str:
        return str(self._get_config_or_default("colors"))

    def set_colors(self, colors: str):
        self._set_config("colors", colors)

    def get_grid_items(self) -> int:
        return int(self._get_config_or_default("grid_items"))

    def set_grid_items(self, grid_items: int):
        self._set_config("grid_items", grid_items)

    def get_hide_watched(self) -> bool:
        return bool(self._get_config_or_default("hide_watched"))

    def set_hide_watched(self, hide_watched: bool):
        self._set_config("hide_watched", hide_watched)

    def get_page_size(self) -> int:
        return int(self._get_config_or_default("page_size"))

    def set_page_size(self, page_size: int):
        self._set_config("page_size", page_size)

    def get_show_ignored_only(self) -> bool:
        return bool(self._get_config_or_default("show_ignored_only"))

    def set_show_ignored_only(self, show_ignored_only: bool):
        self._set_config("show_ignored_only", show_ignored_only)

    def get_show_subed_only(self) -> bool:
        return bool(self._get_config_or_default("show_subed_only"))

    def set_show_subed_only(self, show_subed_only: bool):
        self._set_config("show_subed_only", show_subed_only)

    def get_sort_by(self) -> str:
        return str(self._get_config_or_default("sort_by"))

    def set_sort_by(self, sort_by: str):
        self._set_config("sort_by", sort_by)

    def get_sort_order(self) -> str:
        return str(self._get_config_or_default("sort_order"))

    def set_sort_order(self, sort_order: str):
        self._set_config("sort_order", sort_order)

    def get_sponsorblock_id(self) -> str:
        """get sponsorblock userid or generate one if needed"""
        sb_id = str(self._config.get("sponsorblock_id"))
        if not sb_id:
            sb_id = randomizor(32)
            self._set_config("sponsorblock_id", sb_id)
        return str(sb_id)

    def get_view_style(self, view_name: str) -> str:
        return str(self._get_config_or_default(f"view_style_{view_name}"))

    def set_view_style(self, view_name: str, view_style: str):
        self._set_config(f"view_style_{view_name}", view_style)

    def _get_config_or_default(self, property: str) -> any:
        return self._config.get(property) or self._DEFAULT_USER_SETTINGS.get(
            property
        )

    def _get_config(self) -> dict[str, any]:
        """get config from ES or load from the application defaults"""
        if not self._user_id:
            # this is for a non logged-in user so use all the defaults
            return {}

        # Does this user have configuration stored in ES
        response, status = ElasticWrap(self._document_path).get(
            print_error=False
        )
        if status == 200 and "_source" in response.keys():
            source = response.get("_source")
            if "config" in source.keys():
                return source.get("config")

        # There is no config in ES
        return {}

    def _set_config(self, name: str, value: any):
        if not self._user_id:
            raise ValueError("Unable to persist config for null user_id")

        old = self._config.get(name)
        self._config[name] = value

        es_payload = {"config": self._config}
        ElasticWrap(self._document_path).put(es_payload)

        msg = f"User {self._user_id} property '{name}' change: {old} > {value}"
        print(msg)
