"""
functionality:
- base class to make all calls to yt-dlp
- handle yt-dlp errors
"""

from time import sleep

import yt_dlp


class YtWrap:
    """wrap calls to yt"""

    def __init__(self, obs):
        self.obs = obs

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
        response = yt_dlp.YoutubeDL(self.obs).extract_info(url)

        return response
