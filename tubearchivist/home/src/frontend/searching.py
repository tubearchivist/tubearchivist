"""
Functionality:
- handle search to populate results to view
- cache youtube video thumbnails and channel artwork
- parse values in hit_cleanup for frontend
- calculate pagination values
"""

import urllib.parse
from datetime import datetime

from home.src.download.thumbnails import ThumbManager
from home.src.es.connect import ElasticWrap
from home.src.ta.config import AppConfig


class SearchHandler:
    """search elastic search"""

    def __init__(self, path, config, data=False):
        self.max_hits = None
        self.path = path
        self.config = config
        self.data = data

    def get_data(self):
        """get the data"""
        response, _ = ElasticWrap(self.path, config=self.config).get(self.data)

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

        if "playlist_last_refresh" in hit_keys:
            playlist_last_refresh = hit["source"]["playlist_last_refresh"]
            date_refresh = datetime.fromtimestamp(playlist_last_refresh)
            date_str = datetime.strftime(date_refresh, "%d %b, %Y")
            hit["source"]["playlist_last_refresh"] = date_str

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

    def multi_search(self, search_query):
        """searching through index"""
        path = "ta_video,ta_channel,ta_playlist/_search"
        data = {
            "size": 30,
            "query": {
                "multi_match": {
                    "query": search_query,
                    "type": "bool_prefix",
                    "operator": "and",
                    "fuzziness": "auto",
                    "fields": [
                        "category",
                        "channel_description",
                        "channel_name._2gram",
                        "channel_name._3gram",
                        "channel_name.search_as_you_type",
                        "playlist_description",
                        "playlist_name._2gram",
                        "playlist_name._3gram",
                        "playlist_name.search_as_you_type",
                        "tags",
                        "title._2gram",
                        "title._3gram",
                        "title.search_as_you_type",
                    ],
                }
            },
        }
        look_up = SearchHandler(path, config=self.CONFIG, data=data)
        search_results = look_up.get_data()
        all_results = self.build_results(search_results)

        return {"results": all_results}

    @staticmethod
    def build_results(search_results):
        """build the all_results dict"""
        video_results = []
        channel_results = []
        playlist_results = []
        if search_results:
            for result in search_results:
                if result["_index"] == "ta_video":
                    video_results.append(result)
                elif result["_index"] == "ta_channel":
                    channel_results.append(result)
                elif result["_index"] == "ta_playlist":
                    playlist_results.append(result)

        all_results = {
            "video_results": video_results,
            "channel_results": channel_results,
            "playlist_results": playlist_results,
        }

        return all_results
