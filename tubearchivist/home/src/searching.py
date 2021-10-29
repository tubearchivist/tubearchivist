"""
Functionality:
- handle search to populate results to view
- cache youtube video thumbnails and channel artwork
- parse values in hit_cleanup for frontend
- calculate pagination values
"""

import math
import urllib.parse
from datetime import datetime

import requests
from home.src.config import AppConfig
from home.src.helper import RedisArchivist
from home.src.thumbnails import ThumbManager


class SearchHandler:
    """search elastic search"""

    CONFIG = AppConfig().config
    CACHE_DIR = CONFIG["application"]["cache_dir"]
    ES_AUTH = CONFIG["application"]["es_auth"]

    def __init__(self, url, data):
        self.max_hits = None
        self.url = url
        self.data = data

    def get_data(self):
        """get the data"""
        if self.data:
            response = requests.get(
                self.url, json=self.data, auth=self.ES_AUTH
            ).json()
        else:
            response = requests.get(self.url, auth=self.ES_AUTH).json()

        if "hits" in response.keys():
            self.max_hits = response["hits"]["total"]["value"]
            return_value = response["hits"]["hits"]
        else:
            # simulate list for single result to reuse rest of class
            return_value = [response]

        # stop if empty
        if not return_value:
            return False

        all_videos = []
        all_channels = []
        for idx, hit in enumerate(return_value):
            return_value[idx] = self.hit_cleanup(hit)
            if hit["_index"] == "ta_video":
                video_dict, channel_dict = self.vid_cache_link(hit)
                if video_dict not in all_videos:
                    all_videos.append(video_dict)
                if channel_dict not in all_channels:
                    all_channels.append(channel_dict)
            elif hit["_index"] == "ta_channel":
                channel_dict = self.channel_cache_link(hit)
                if channel_dict not in all_channels:
                    all_channels.append(channel_dict)

        return return_value

    @staticmethod
    def vid_cache_link(hit):
        """download thumbnails into cache"""
        vid_thumb = hit["source"]["vid_thumb_url"]
        youtube_id = hit["source"]["youtube_id"]
        channel_id_hit = hit["source"]["channel"]["channel_id"]
        chan_thumb = hit["source"]["channel"]["channel_thumb_url"]
        try:
            chan_banner = hit["source"]["channel"]["channel_banner_url"]
        except KeyError:
            chan_banner = False
        video_dict = {"youtube_id": youtube_id, "vid_thumb": vid_thumb}
        channel_dict = {
            "channel_id": channel_id_hit,
            "chan_thumb": chan_thumb,
            "chan_banner": chan_banner,
        }
        return video_dict, channel_dict

    @staticmethod
    def channel_cache_link(hit):
        """build channel thumb links"""
        channel_id_hit = hit["source"]["channel_id"]
        chan_thumb = hit["source"]["channel_thumb_url"]
        try:
            chan_banner = hit["source"]["channel_banner_url"]
        except KeyError:
            chan_banner = False
        channel_dict = {
            "channel_id": channel_id_hit,
            "chan_thumb": chan_thumb,
            "chan_banner": chan_banner,
        }
        return channel_dict

    @staticmethod
    def hit_cleanup(hit):
        """clean up and parse data from a single hit"""
        hit["source"] = hit.pop("_source")
        hit_keys = hit["source"].keys()
        if "media_url" in hit_keys:
            parsed_url = urllib.parse.quote(hit["source"]["media_url"])
            hit["source"]["media_url"] = parsed_url

        if "published" in hit_keys:
            published = hit["source"]["published"]
            date_pub = datetime.strptime(published, "%Y-%m-%d")
            date_str = datetime.strftime(date_pub, "%d %b, %Y")
            hit["source"]["published"] = date_str

        if "vid_last_refresh" in hit_keys:
            vid_last_refresh = hit["source"]["vid_last_refresh"]
            date_refresh = datetime.fromtimestamp(vid_last_refresh)
            date_str = datetime.strftime(date_refresh, "%d %b, %Y")
            hit["source"]["vid_last_refresh"] = date_str

        if "vid_thumb_url" in hit_keys:
            youtube_id = hit["source"]["youtube_id"]
            thumb_path = ThumbManager().vid_thumb_path(youtube_id)
            hit["source"]["vid_thumb_url"] = thumb_path

        if "channel_last_refresh" in hit_keys:
            refreshed = hit["source"]["channel_last_refresh"]
            date_refresh = datetime.fromtimestamp(refreshed)
            date_str = datetime.strftime(date_refresh, "%d %b, %Y")
            hit["source"]["channel_last_refresh"] = date_str

        if "channel" in hit_keys:
            channel_keys = hit["source"]["channel"].keys()
            if "channel_last_refresh" in channel_keys:
                refreshed = hit["source"]["channel"]["channel_last_refresh"]
                date_refresh = datetime.fromtimestamp(refreshed)
                date_str = datetime.strftime(date_refresh, "%d %b, %Y")
                hit["source"]["channel"]["channel_last_refresh"] = date_str

        return hit


class SearchForm:
    """build query from search form data"""

    CONFIG = AppConfig().config
    ES_URL = CONFIG["application"]["es_url"]

    def search_channels(self, search_query):
        """fancy searching channels as you type"""
        url = self.ES_URL + "/ta_channel/_search"
        data = {
            "size": 10,
            "query": {
                "multi_match": {
                    "query": search_query,
                    "type": "bool_prefix",
                    "fields": [
                        "channel_name.search_as_you_type",
                        "channel_name._2gram",
                        "channel_name._3gram",
                    ],
                }
            },
        }
        look_up = SearchHandler(url, data)
        search_results = look_up.get_data()
        return {"results": search_results}

    @staticmethod
    def search_videos():
        """searching for videos"""
        # TBD palceholder for now
        return False


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
        }
        if self.search_get:
            pagination.update({"search_get": self.search_get})
        return pagination

    def validate(self, total_hits):
        """validate pagination with total_hits after making api call"""
        page_get = self.page_get
        max_pages = math.ceil(total_hits / self.page_size)
        if page_get < max_pages and max_pages > 1:
            self.pagination["last_page"] = max_pages
        else:
            self.pagination["last_page"] = False
        next_pages = [
            i for i in range(page_get + 1, page_get + 6) if 1 < i < max_pages
        ]

        self.pagination["next_pages"] = next_pages
