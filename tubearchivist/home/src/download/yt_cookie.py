"""
functionality:
- import yt cookie from filesystem
- make cookie available for yt-dlp
"""

import os

import yt_dlp
from home.src.ta.config import AppConfig
from home.src.ta.ta_redis import RedisArchivist


class CookieHandler:
    """handle youtube cookie for yt-dlp"""

    CONFIG = AppConfig().config
    CACHE_PATH = CONFIG["application"]["cache_dir"]
    COOKIE_FILE_NAME = "cookies.google.txt"
    COOKIE_KEY = "cookie"
    COOKIE_PATH = "cookie.txt"

    def import_cookie(self):
        """import cookie from file"""
        import_path = os.path.join(
            self.CACHE_PATH, "import", self.COOKIE_FILE_NAME
        )
        with open(import_path, encoding="utf-8") as cookie_file:
            cookie = cookie_file.read()

        RedisArchivist().set_message(self.COOKIE_KEY, cookie, expire=False)

        os.remove(import_path)
        print("cookie: import successfully")

    def use(self):
        """make cookie available in FS"""
        cookie = RedisArchivist().get_message(self.COOKIE_KEY)
        with open(self.COOKIE_PATH, "w", encoding="utf-8") as cookie_file:
            cookie_file.write(cookie)

        print("cookie: made available")
        return self.COOKIE_PATH

    def hide(self):
        """hide cookie file if not in use"""
        try:
            os.remove(self.COOKIE_PATH)
        except FileNotFoundError:
            print("cookie: not available")
            return

        print("cookie: hidden")

    def revoke(self):
        """revoke cookie"""
        self.hide()
        RedisArchivist().del_message(self.COOKIE_KEY)
        print("cookie: revoked")

    def validate(self):
        """validate cookie using the liked videos playlist"""
        _ = self.use()
        url = "https://www.youtube.com/playlist?list=LL"
        yt_obs = {
            "quiet": True,
            "skip_download": True,
            "extract_flat": True,
            "cookiefile": self.COOKIE_PATH,
        }
        try:
            response = yt_dlp.YoutubeDL(yt_obs).extract_info(url)
        except yt_dlp.utils.DownloadError:
            print("failed to validate cookie")
            response = False

        return bool(response)
