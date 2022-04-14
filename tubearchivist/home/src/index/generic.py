"""
functionality:
- generic base class to inherit from for video, channel and playlist
"""

import math

import yt_dlp
from home.src.es.connect import ElasticWrap
from home.src.ta.config import AppConfig
from home.src.ta.ta_redis import RedisArchivist


class YouTubeItem:
    """base class for youtube"""

    es_path = False
    index_name = False
    yt_base = False
    yt_obs = {
        "quiet": True,
        "default_search": "ytsearch",
        "skip_download": True,
        "check_formats": "selected",
        "noplaylist": True,
    }

    def __init__(self, youtube_id):
        self.youtube_id = youtube_id
        self.config = False
        self.app_conf = False
        self.youtube_meta = False
        self.json_data = False
        self._get_conf()

    def _get_conf(self):
        """read user conf"""
        self.config = AppConfig().config
        self.app_conf = self.config["application"]

    def get_from_youtube(self):
        """use yt-dlp to get meta data from youtube"""
        print(f"{self.youtube_id}: get metadata from youtube")
        try:
            yt_item = yt_dlp.YoutubeDL(self.yt_obs)
            response = yt_item.extract_info(self.yt_base + self.youtube_id)
        except (
            yt_dlp.utils.ExtractorError,
            yt_dlp.utils.DownloadError,
        ):
            print(f"{self.youtube_id}: failed to get info from youtube")
            response = False

        self.youtube_meta = response

    def get_from_es(self):
        """get indexed data from elastic search"""
        print(f"{self.youtube_id}: get metadata from es")
        response, _ = ElasticWrap(f"{self.es_path}").get()
        source = response.get("_source")
        self.json_data = source

    def upload_to_es(self):
        """add json_data to elastic"""
        _, _ = ElasticWrap(self.es_path).put(self.json_data, refresh=True)

    def deactivate(self):
        """deactivate document in es"""
        print(f"{self.youtube_id}: deactivate document")
        key_match = {
            "ta_video": "active",
            "ta_channel": "channel_active",
            "ta_playlist": "playlist_active",
        }
        update_path = f"{self.index_name}/_update/{self.youtube_id}"
        data = {
            "script": f"ctx._source.{key_match.get(self.index_name)} = false"
        }
        _, _ = ElasticWrap(update_path).post(data)

    def del_in_es(self):
        """delete item from elastic search"""
        print(f"{self.youtube_id}: delete from es")
        _, _ = ElasticWrap(self.es_path).delete()


class Pagination:
    """
    figure out the pagination based on page size and total_hits
    """

    def __init__(self, page_get, user_id, search_get=False):
        self.user_id = user_id
        self.page_size = self.get_page_size()
        self.page_get = page_get
        self.search_get = search_get
        self.pagination = self.first_guess()

    def get_page_size(self):
        """get default or user modified page_size"""
        key = f"{self.user_id}:page_size"
        page_size = RedisArchivist().get_message(key)["status"]
        if not page_size:
            config = AppConfig().config
            page_size = config["archive"]["page_size"]

        return page_size

    def first_guess(self):
        """build first guess before api call"""
        page_get = self.page_get
        if page_get in [0, 1]:
            page_from = 0
            prev_pages = False
        elif page_get > 1:
            page_from = (page_get - 1) * self.page_size
            prev_pages = [
                i for i in range(page_get - 1, page_get - 6, -1) if i > 1
            ]
            prev_pages.reverse()
        pagination = {
            "page_size": self.page_size,
            "page_from": page_from,
            "prev_pages": prev_pages,
            "current_page": page_get,
            "max_hits": False,
        }
        if self.search_get:
            pagination.update({"search_get": self.search_get})
        return pagination

    def validate(self, total_hits):
        """validate pagination with total_hits after making api call"""
        page_get = self.page_get
        max_pages = math.ceil(total_hits / self.page_size)
        if total_hits >= 10000:
            # es returns maximal 10000 results
            self.pagination["max_hits"] = True
            max_pages = max_pages - 1

        if page_get < max_pages and max_pages > 1:
            self.pagination["last_page"] = max_pages
        else:
            self.pagination["last_page"] = False
        next_pages = [
            i for i in range(page_get + 1, page_get + 6) if 1 < i < max_pages
        ]

        self.pagination["next_pages"] = next_pages
