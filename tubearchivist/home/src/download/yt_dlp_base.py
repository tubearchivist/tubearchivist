"""
functionality:
- base class to make all calls to yt-dlp
- handle yt-dlp errors
"""

from time import sleep

import yt_dlp


class YtWrap:
    """wrap calls to yt"""

    OBS_BASE = {
        "default_search": "ytsearch",
        "quiet": True,
        "check_formats": "selected",
        "socket_timeout": 2,
    }

    def __init__(self, obs_request):
        self.obs_request = obs_request
        self.build_obs()

    def build_obs(self):
        """build yt-dlp obs"""
        self.obs = self.OBS_BASE.copy()
        self.obs.update(self.obs_request)

    def download(self, url):
        """make download request"""

        with yt_dlp.YoutubeDL(self.obs) as ydl:
            try:
                ydl.download([url])
            except yt_dlp.utils.DownloadError:
                print(f"{url}: failed to download, retry...")
                sleep(3)
                ydl.download([url])

    def extract(self, url):
        """make extract request"""
        try:
            response = yt_dlp.YoutubeDL(self.obs).extract_info(url)
        except (yt_dlp.utils.ExtractorError, yt_dlp.utils.DownloadError):
            print(f"{url}: failed to get info from youtube")
            response = False

        return response
