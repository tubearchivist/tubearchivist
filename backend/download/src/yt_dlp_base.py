"""
functionality:
- base class to make all calls to yt-dlp
- handle yt-dlp errors
"""

from datetime import datetime
from http import cookiejar
from io import StringIO

import yt_dlp
from appsettings.src.config import AppConfig
from common.src.ta_redis import RedisArchivist
from django.conf import settings


class YtWrap:
    """wrap calls to yt"""

    OBS_BASE = {
        "default_search": "ytsearch",
        "quiet": True,
        "check_formats": "selected",
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
                            "player-client": ["web", "default"],
                        },
                    }
                }
            )

    def download(self, url):
        """make download request"""
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

    def extract(self, url):
        """make extract request"""
        with yt_dlp.YoutubeDL(self.obs) as ydl:
            try:
                response = ydl.extract_info(url)
            except cookiejar.LoadError as err:
                print(f"cookie file is invalid: {err}")
                return False
            except yt_dlp.utils.ExtractorError as err:
                print(f"{url}: failed to extract: {err}, continue...")
                return False
            except yt_dlp.utils.DownloadError as err:
                if "This channel does not have a" in str(err):
                    return False

                print(f"{url}: failed to get info from youtube: {err}")
                if "Temporary failure in name resolution" in str(err):
                    raise ConnectionError("lost the internet, abort!") from err

                return False

        self._validate_cookie()

        return response

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
        AppConfig().update_config({"downloads.cookie_import": True})
        self.config["downloads"]["cookie_import"] = True
        print("[cookie]: activated and stored in Redis")

    @staticmethod
    def revoke():
        """revoke cookie"""
        RedisArchivist().del_message("cookie")
        RedisArchivist().del_message("cookie:valid")
        AppConfig().update_config({"downloads.cookie_import": False})
        print("[cookie]: revoked")

    def validate(self):
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
        response = bool(validator.extract("LL"))
        self.store_validation(response)

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
                "message": "",
            }
            RedisArchivist().set_message(
                "message:download", mess_dict, expire=4
            )
            print("[cookie]: validation failed, exiting...")

        print(f"[cookie]: validation success: {response}")
        return response

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
        AppConfig().update_config({"downloads.potoken": True})

    def revoke_token(self) -> None:
        """revoke token"""
        RedisArchivist().del_message(self.REDIS_KEY)
        AppConfig().update_config({"downloads.potoken": False})
