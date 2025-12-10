"""
functionality:
- base class to make all calls to yt-dlp
- handle yt-dlp errors
"""

import re
from datetime import datetime
from http import cookiejar
from io import StringIO

import yt_dlp
from appsettings.src.config import AppConfig
from common.src.ta_redis import RedisArchivist
from django.conf import settings


class ExtractorArgsParser:
    """
    Parse extractor_args string following yt-dlp format.

    Format: "extractor1:key1=val1,val2;key2=val3 extractor2:key3=val4"

    - Whitespace separates multiple extractors
    - Colon (:) separates extractor name from key-value pairs
    - Semicolon (;) separates multiple key-value pairs
    - Equals (=) separates key from values
    - Comma (,) separates multiple values (escaped commas \\, are preserved)

    Example:
        >>> parser = ExtractorArgsParser()
        >>> result = parser.parse("youtube:key1=val1,val2;key2=val3")
        >>> # Returns: {"youtube": {"key1": ["val1", "val2"],
        >>> #              "key2": ["val3"]}}
    """

    @staticmethod
    def _parse_key_values(key, vals=""):
        """
        Parse a single key=values pair following yt-dlp logic.

        Args:
            key: The key name (will be normalized)
            vals: Comma-separated values (escaped commas preserved)

        Returns:
            tuple: (normalized_key, list_of_values)
        """
        # Normalize key: strip, lowercase, replace hyphens with underscores
        normalized_key = key.strip().lower().replace("-", "_")

        # Split values by comma, but preserve escaped commas
        # yt-dlp uses: re.split(r'(?<!\\),', vals)
        if not vals:
            return normalized_key, []

        value_list = [
            val.replace(r"\,", ",").strip()
            for val in re.split(r"(?<!\\),", vals)
        ]

        return normalized_key, value_list

    def parse(self, extractor_args_str):
        """
        Parse extractor_args string into nested dictionary structure.

        Args:
            extractor_args_str: String in format "extractor:key=val;key2=val2"

        Returns:
            dict: Nested dictionary with structure:
                  {extractor_name: {key: [values]}}

        Example:
            >>> parser.parse("youtube:lang=en,es;key2=val generic:key3=val3")
            {'youtube': {'lang': ['en', 'es'], 'key2': ['val']},
             'generic': {'key3': ['val3']}}
        """
        if not extractor_args_str or not extractor_args_str.strip():
            return {}

        result = {}

        # Split by whitespace to get individual extractor specifications
        extractor_specs = extractor_args_str.strip().split()

        for spec in extractor_specs:
            # Split by first colon to separate extractor from args
            if ":" not in spec:
                print(
                    "[extractor_args] Warning: Invalid format "
                    f"(missing colon): {spec}"
                )
                continue

            extractor_name, args_part = spec.split(":", 1)
            extractor_name = extractor_name.strip()

            if not extractor_name:
                print(
                    "[extractor_args] Warning: Empty extractor name "
                    f"in: {spec}"
                )
                continue

            # Initialize extractor dict if not exists
            if extractor_name not in result:
                result[extractor_name] = {}

            # Split args by semicolon to get individual key=value pairs
            key_value_pairs = args_part.split(";")

            for pair in key_value_pairs:
                if not pair.strip():
                    continue

                # Split by first equals sign
                if "=" not in pair:
                    print(
                        "[extractor_args] Warning: Invalid pair "
                        f"(missing =): {pair}"
                    )
                    continue

                key_part, value_part = pair.split("=", 1)
                normalized_key, value_list = self._parse_key_values(
                    key_part, value_part
                )

                result[extractor_name][normalized_key] = value_list

        return result


class YtWrap:
    """wrap calls to yt"""

    OBS_BASE = {
        "default_search": "ytsearch",
        "quiet": True,
        "socket_timeout": 10,
        "extractor_retries": 3,
        "retries": 10,
    }

    def __init__(self, obs_request, config=False):
        self.obs_request = obs_request
        self.config = config
        self.build_obs()

    def build_obs(self):
        """build yt-dlp obs"""
        self.obs = self.OBS_BASE.copy()
        self.obs.update(self.obs_request)
        if self.config:
            self._add_cookie()
            self._add_potoken()
            self._add_extractor_args()

        if getattr(settings, "DEBUG", False):
            del self.obs["quiet"]
            print(self.obs)

    def _add_cookie(self):
        """add cookie if enabled"""
        if self.config["downloads"]["cookie_import"]:
            cookie_io = CookieHandler(self.config).get()
            self.obs["cookiefile"] = cookie_io

    def _add_potoken(self):
        """add potoken if enabled"""
        if self.config["downloads"].get("potoken"):
            potoken = POTokenHandler(self.config).get()
            self.obs.update(
                {
                    "extractor_args": {
                        "youtube": {
                            "po_token": [potoken],
                            "player-client": ["mweb", "default"],
                        },
                    }
                }
            )

    def _add_extractor_args(self):
        """add custom extractor_args from config if present"""
        extractor_args_str = self.config["downloads"].get("extractor_args")
        pot_provider_url = self.config["downloads"].get("pot_provider_url")

        # If pot_provider_url is set, append it to extractor_args
        if pot_provider_url:
            pot_arg = f"youtubepot-bgutilhttp:base_url={pot_provider_url}"
            if extractor_args_str:
                extractor_args_str = f"{extractor_args_str} {pot_arg}"
            else:
                extractor_args_str = pot_arg

        if not extractor_args_str:
            return

        # Parse the extractor_args string
        parser = ExtractorArgsParser()
        parsed_args = parser.parse(extractor_args_str)

        if not parsed_args:
            return

        # Merge with existing extractor_args if present
        if "extractor_args" not in self.obs:
            self.obs["extractor_args"] = {}

        for extractor_name, args_dict in parsed_args.items():
            if extractor_name not in self.obs["extractor_args"]:
                self.obs["extractor_args"][extractor_name] = {}

            # Merge the arguments, with parsed args taking precedence
            self.obs["extractor_args"][extractor_name].update(args_dict)

        print(f"[extractor_args] Applied custom args: {parsed_args}")

    def download(self, url):
        """make download request"""
        self.obs.update({"check_formats": "selected"})
        with yt_dlp.YoutubeDL(self.obs) as ydl:
            try:
                ydl.download([url])
            except yt_dlp.utils.DownloadError as err:
                print(f"{url}: failed to download with message {err}")
                if "Temporary failure in name resolution" in str(err):
                    raise ConnectionError("lost the internet, abort!") from err

                return False, str(err)

        self._validate_cookie()

        return True, True

    def extract(self, url) -> tuple[dict | None, str | None]:
        """
        make extract request
        returns response, error
        """
        with yt_dlp.YoutubeDL(self.obs) as ydl:
            try:
                response = ydl.extract_info(url)
            except cookiejar.LoadError as err:
                print(f"cookie file is invalid: {err}")
                return None, str(err)
            except yt_dlp.utils.ExtractorError as err:
                print(f"{url}: failed to extract: {err}, continue...")
                return None, str(err)
            except yt_dlp.utils.DownloadError as err:
                if "This channel does not have a" in str(err):
                    return None, None

                print(f"{url}: failed to get info from youtube: {err}")
                if "Temporary failure in name resolution" in str(err):
                    raise ConnectionError("lost the internet, abort!") from err

                return None, str(err)

        self._validate_cookie()

        return response, None

    def _validate_cookie(self):
        """check cookie and write it back for next use"""
        if not self.obs.get("cookiefile"):
            return

        new_cookie = self.obs["cookiefile"].read()
        old_cookie = RedisArchivist().get_message_str("cookie")
        if new_cookie and old_cookie != new_cookie:
            print("refreshed stored cookie")
            RedisArchivist().set_message("cookie", new_cookie, save=True)


class CookieHandler:
    """handle youtube cookie for yt-dlp"""

    def __init__(self, config):
        self.cookie_io = False
        self.config = config

    def get(self):
        """get cookie io stream"""
        cookie = RedisArchivist().get_message_str("cookie")
        self.cookie_io = StringIO(cookie)
        return self.cookie_io

    def set_cookie(self, cookie):
        """set cookie str and activate in config"""
        cookie_clean = cookie.strip("\x00")
        RedisArchivist().set_message("cookie", cookie_clean, save=True)
        AppConfig().update_config({"downloads": {"cookie_import": True}})
        self.config["downloads"]["cookie_import"] = True
        print("[cookie]: activated and stored in Redis")

    @staticmethod
    def revoke():
        """revoke cookie"""
        RedisArchivist().del_message("cookie")
        RedisArchivist().del_message("cookie:valid")
        AppConfig().update_config({"downloads": {"cookie_import": False}})
        print("[cookie]: revoked")

    def validate(self) -> bool:
        """validate cookie using the liked videos playlist"""
        validation = RedisArchivist().get_message_dict("cookie:valid")
        if validation:
            print("[cookie]: used cached cookie validation")
            return True

        print("[cookie] validating cookie")
        obs_request = {
            "skip_download": True,
            "extract_flat": True,
        }
        validator = YtWrap(obs_request, self.config)
        response, error = validator.extract("LL")
        self.store_validation(bool(response))

        # update in redis to avoid expiring
        modified = validator.obs["cookiefile"].getvalue().strip("\x00")
        if modified:
            cookie_clean = modified.strip("\x00")
            RedisArchivist().set_message("cookie", cookie_clean)

        if not response:
            mess_dict = {
                "status": "message:download",
                "level": "error",
                "title": "Cookie validation failed, exiting...",
                "message": error,
            }
            RedisArchivist().set_message(
                "message:download", mess_dict, expire=4
            )
            print("[cookie]: validation failed, exiting...")

        print(f"[cookie]: validation success: {bool(response)}")
        return bool(response)

    @staticmethod
    def store_validation(response):
        """remember last validation"""
        now = datetime.now()
        message = {
            "status": response,
            "validated": int(now.timestamp()),
            "validated_str": now.strftime("%Y-%m-%d %H:%M"),
        }
        RedisArchivist().set_message("cookie:valid", message, expire=3600)


class POTokenHandler:
    """handle po token"""

    REDIS_KEY = "potoken"

    def __init__(self, config):
        self.config = config

    def get(self) -> str | None:
        """get PO token"""
        potoken = RedisArchivist().get_message_str(self.REDIS_KEY)
        return potoken

    def set_token(self, new_token: str) -> None:
        """set new PO token"""
        RedisArchivist().set_message(self.REDIS_KEY, new_token)
        AppConfig().update_config({"downloads": {"potoken": True}})

    def revoke_token(self) -> None:
        """revoke token"""
        RedisArchivist().del_message(self.REDIS_KEY)
        AppConfig().update_config({"downloads": {"potoken": False}})
