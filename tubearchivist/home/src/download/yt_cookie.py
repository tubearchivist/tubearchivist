"""
functionality:
- import yt cookie from filesystem
- make cookie available for yt-dlp
"""

import os

from home.src.ta.config import AppConfig
from home.src.ta.ta_redis import RedisArchivist


class CookieHandler:
    """handle youtube cookie for yt-dlp"""

    CONFIG = AppConfig().config
    CACHE_PATH = CONFIG["application"]["cache_dir"]
    COOKIE_FILE_NAME = "cookies.google.txt"

    def __init__(self, user_id):
        self.cookie_path = f"cookie_{user_id}.txt"
        self.cookie_key = f"{user_id}:cookie"

    def import_cookie(self):
        """import cookie from file"""
        import_path = os.path.join(
            self.CACHE_PATH, "import", self.COOKIE_FILE_NAME
        )
        with open(import_path, encoding="utf-8") as cookie_file:
            cookie = cookie_file.read()

        RedisArchivist().set_message(self.cookie_key, cookie, expire=False)

        os.remove(import_path)
        print("cookie: import successfully")

    def use(self):
        """make cookie available in FS"""
        cookie = RedisArchivist().get_message(self.cookie_key)
        with open(self.cookie_path, "w", encoding="utf-8") as cookie_file:
            cookie_file.write(cookie)

        print("cookie: made available")
        return self.cookie_path

    def hide(self):
        """hide cookie file if not in use"""
        try:
            os.remove(self.cookie_path)
        except FileExistsError:
            print("cookie: not available")
            return

        print("cookie: hidden")

    def revoke(self):
        """revoke cookie"""
        self.hide()
        RedisArchivist().del_message(self.cookie_key)
        print("cookie: revoked")
