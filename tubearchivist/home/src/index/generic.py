"""
functionality:
- generic base class to inherit from for video, channel and playlist
"""

import math

from home.src.download.yt_dlp_base import YtWrap
from home.src.es.connect import ElasticWrap
from home.src.ta.config import AppConfig
from home.src.ta.users import UserConfig


class YouTubeItem:
    """base class for youtube"""

    es_path = False
    index_name = ""
    yt_base = ""
    yt_obs: dict[str, bool | str] = {
        "skip_download": True,
        "noplaylist": True,
    }

    def __init__(self, youtube_id):
        self.youtube_id = youtube_id
        self.es_path = f"{self.index_name}/_doc/{youtube_id}"
        self.config = AppConfig().config
        self.youtube_meta = False
        self.json_data = False

    def build_yt_url(self):
        """build youtube url"""
        return self.yt_base + self.youtube_id

    def get_from_youtube(self):
        """use yt-dlp to get meta data from youtube"""
        print(f"{self.youtube_id}: get metadata from youtube")
        obs_request = self.yt_obs.copy()
        if self.config["downloads"]["extractor_lang"]:
            langs = self.config["downloads"]["extractor_lang"]
            langs_list = [i.strip() for i in langs.split(",")]
            obs_request["extractor_args"] = {"youtube": {"lang": langs_list}}

        url = self.build_yt_url()
        self.youtube_meta = YtWrap(obs_request, self.config).extract(url)

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
        path = f"{self.index_name}/_update/{self.youtube_id}?refresh=true"
        data = {
            "script": f"ctx._source.{key_match.get(self.index_name)} = false"
        }
        _, _ = ElasticWrap(path).post(data)

    def del_in_es(self):
        """delete item from elastic search"""
        print(f"{self.youtube_id}: delete from es")
        _, _ = ElasticWrap(self.es_path).delete(refresh=True)


class Pagination:
    """
    figure out the pagination based on page size and total_hits
    """

    def __init__(self, request):
        self.request = request
        self.page_get = False
        self.params = False
        self.get_params()
        self.page_size = self.get_page_size()
        self.pagination = self.first_guess()

    def get_params(self):
        """process url query parameters"""
        query_dict = self.request.GET.copy()
        self.page_get = int(query_dict.get("page", 0))

        _ = query_dict.pop("page", False)
        self.params = query_dict.urlencode()

    def get_page_size(self):
        """get default or user modified page_size"""
        return UserConfig(self.request.user.id).get_value("page_size")

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
            "params": self.params,
        }

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
        self.pagination["total_hits"] = total_hits
