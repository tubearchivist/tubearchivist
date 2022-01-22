"""
Functionality:
- index new videos into elastisearch
- extract video info with yt_dlp
- scrape youtube channel page if needed
"""

import json
import os
import re
from datetime import datetime

import requests
import yt_dlp
from bs4 import BeautifulSoup
from home.src.config import AppConfig
from home.src.es import ElasticWrap, IndexPaginate
from home.src.helper import DurationConverter, UrlListParser, clean_string
from home.src.thumbnails import ThumbManager
from ryd_client import ryd_client


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
            self.youtube_meta = False

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
        key_match = {
            "video": "active",
            "channel": "channel_active",
            "playlist": "playlist_active",
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


class YoutubeVideo(YouTubeItem):
    """represents a single youtube video"""

    es_path = False
    index_name = "ta_video"
    yt_base = "https://www.youtube.com/watch?v="

    def __init__(self, youtube_id):
        super().__init__(youtube_id)
        self.channel_id = False
        self.es_path = f"{self.index_name}/_doc/{youtube_id}"

    def build_json(self):
        """build json dict of video"""
        self.get_from_youtube()
        if not self.youtube_meta:
            return

        self._process_youtube_meta()
        self._add_channel()
        self._add_stats()
        self.add_file_path()
        self.add_player()
        if self.config["downloads"]["integrate_ryd"]:
            self._get_ryd_stats()

        return

    def _process_youtube_meta(self):
        """extract relevant fields from youtube"""
        # extract
        self.channel_id = self.youtube_meta["channel_id"]
        upload_date = self.youtube_meta["upload_date"]
        upload_date_time = datetime.strptime(upload_date, "%Y%m%d")
        published = upload_date_time.strftime("%Y-%m-%d")
        last_refresh = int(datetime.now().strftime("%s"))
        # build json_data basics
        self.json_data = {
            "title": self.youtube_meta["title"],
            "description": self.youtube_meta["description"],
            "category": self.youtube_meta["categories"],
            "vid_thumb_url": self.youtube_meta["thumbnail"],
            "tags": self.youtube_meta["tags"],
            "published": published,
            "vid_last_refresh": last_refresh,
            "date_downloaded": last_refresh,
            "youtube_id": self.youtube_id,
            "active": True,
        }

    def _add_channel(self):
        """add channel dict to video json_data"""
        channel = YoutubeChannel(self.channel_id)
        channel.build_json(upload=True)
        self.json_data.update({"channel": channel.json_data})

    def _add_stats(self):
        """add stats dicst to json_data"""
        # likes
        like_count = self.youtube_meta.get("like_count", 0)
        dislike_count = self.youtube_meta.get("dislike_count", 0)
        self.json_data.update(
            {
                "stats": {
                    "view_count": self.youtube_meta["view_count"],
                    "like_count": like_count,
                    "dislike_count": dislike_count,
                    "average_rating": self.youtube_meta["average_rating"],
                }
            }
        )

    def build_dl_cache_path(self):
        """find video path in dl cache"""
        cache_dir = self.app_conf["cache_dir"]
        cache_path = f"{cache_dir}/download/"
        all_cached = os.listdir(cache_path)
        for file_cached in all_cached:
            if self.youtube_id in file_cached:
                vid_path = os.path.join(cache_path, file_cached)
                return vid_path

        return False

    def add_player(self):
        """add player information for new videos"""
        try:
            # when indexing from download task
            vid_path = self.build_dl_cache_path()
        except FileNotFoundError:
            # when reindexing
            base = self.app_conf["videos"]
            vid_path = os.path.join(base, self.json_data["media_url"])

        duration_handler = DurationConverter()
        duration = duration_handler.get_sec(vid_path)
        duration_str = duration_handler.get_str(duration)
        self.json_data.update(
            {
                "player": {
                    "watched": False,
                    "duration": duration,
                    "duration_str": duration_str,
                }
            }
        )

    def add_file_path(self):
        """build media_url for where file will be located"""
        channel_name = self.json_data["channel"]["channel_name"]
        clean_channel_name = clean_string(channel_name)
        timestamp = self.json_data["published"].replace("-", "")
        youtube_id = self.json_data["youtube_id"]
        title = self.json_data["title"]
        clean_title = clean_string(title)
        filename = f"{timestamp}_{youtube_id}_{clean_title}.mp4"
        media_url = os.path.join(clean_channel_name, filename)
        self.json_data["media_url"] = media_url

    def delete_media_file(self):
        """delete video file, meta data"""
        self.get_from_es()
        video_base = self.app_conf["videos"]
        media_url = self.json_data["media_url"]
        print(f"{self.youtube_id}: delete {media_url} from file system")
        to_delete = os.path.join(video_base, media_url)
        os.remove(to_delete)
        self.del_in_es()

    def _get_ryd_stats(self):
        """get optional stats from returnyoutubedislikeapi.com"""
        try:
            print(f"{self.youtube_id}: get ryd stats")
            result = ryd_client.get(self.youtube_id)
        except requests.exceptions.ConnectionError:
            print(f"{self.youtube_id}: failed to query ryd api, skipping")
            return False

        if result["status"] == 404:
            return False

        dislikes = {
            "dislike_count": result["dislikes"],
            "average_rating": result["rating"],
        }
        self.json_data["stats"].update(dislikes)

        return True


class ChannelScraper:
    """custom scraper using bs4 to scrape channel about page
    will be able to be integrated into yt-dlp
    once #2237 and #2350 are merged upstream
    """

    def __init__(self, channel_id):
        self.channel_id = channel_id
        self.soup = False
        self.yt_json = False
        self.json_data = False

    def get_json(self):
        """main method to return channel dict"""
        self.get_soup()
        self._extract_yt_json()
        self._parse_channel_main()
        self._parse_channel_meta()
        return self.json_data

    def get_soup(self):
        """return soup from youtube"""
        print(f"{self.channel_id}: scrape channel data from youtube")
        url = f"https://www.youtube.com/channel/{self.channel_id}/about?hl=en"
        cookies = {"CONSENT": "YES+xxxxxxxxxxxxxxxxxxxxxxxxxxx"}
        response = requests.get(url, cookies=cookies)
        if response.ok:
            channel_page = response.text
        else:
            print(f"{self.channel_id}: failed to extract channel info")
            raise ConnectionError
        self.soup = BeautifulSoup(channel_page, "html.parser")

    def _extract_yt_json(self):
        """parse soup and get ytInitialData json"""
        all_scripts = self.soup.find("body").find_all("script")
        for script in all_scripts:
            if "var ytInitialData = " in str(script):
                script_content = str(script)
                break
        # extract payload
        script_content = script_content.split("var ytInitialData = ")[1]
        json_raw = script_content.rstrip(";</script>")
        self.yt_json = json.loads(json_raw)

    def _parse_channel_main(self):
        """extract maintab values from scraped channel json data"""
        main_tab = self.yt_json["header"]["c4TabbedHeaderRenderer"]
        # build and return dict
        self.json_data = {
            "channel_active": True,
            "channel_last_refresh": int(datetime.now().strftime("%s")),
            "channel_subs": self._get_channel_subs(main_tab),
            "channel_name": main_tab["title"],
            "channel_banner_url": self._get_thumbnails(main_tab, "banner"),
            "channel_tvart_url": self._get_thumbnails(main_tab, "tvBanner"),
            "channel_id": self.channel_id,
            "channel_subscribed": False,
        }

    @staticmethod
    def _get_thumbnails(main_tab, thumb_name):
        """extract banner url from main_tab"""
        try:
            all_banners = main_tab[thumb_name]["thumbnails"]
            banner = sorted(all_banners, key=lambda k: k["width"])[-1]["url"]
        except KeyError:
            banner = False

        return banner

    @staticmethod
    def _get_channel_subs(main_tab):
        """process main_tab to get channel subs as int"""
        try:
            sub_text_simple = main_tab["subscriberCountText"]["simpleText"]
            sub_text = sub_text_simple.split(" ")[0]
            if sub_text[-1] == "K":
                channel_subs = int(float(sub_text.replace("K", "")) * 1000)
            elif sub_text[-1] == "M":
                channel_subs = int(float(sub_text.replace("M", "")) * 1000000)
            elif int(sub_text) >= 0:
                channel_subs = int(sub_text)
            else:
                message = f"{sub_text} not dealt with"
                print(message)
        except KeyError:
            channel_subs = 0

        return channel_subs

    def _parse_channel_meta(self):
        """extract meta tab values from channel payload"""
        # meta tab
        meta_tab = self.yt_json["metadata"]["channelMetadataRenderer"]
        all_thumbs = meta_tab["avatar"]["thumbnails"]
        thumb_url = sorted(all_thumbs, key=lambda k: k["width"])[-1]["url"]
        # stats tab
        renderer = "twoColumnBrowseResultsRenderer"
        all_tabs = self.yt_json["contents"][renderer]["tabs"]
        for tab in all_tabs:
            if "tabRenderer" in tab.keys():
                if tab["tabRenderer"]["title"] == "About":
                    about_tab = tab["tabRenderer"]["content"][
                        "sectionListRenderer"
                    ]["contents"][0]["itemSectionRenderer"]["contents"][0][
                        "channelAboutFullMetadataRenderer"
                    ]
                    break
        try:
            channel_views_text = about_tab["viewCountText"]["simpleText"]
            channel_views = int(re.sub(r"\D", "", channel_views_text))
        except KeyError:
            channel_views = 0

        self.json_data.update(
            {
                "channel_description": meta_tab["description"],
                "channel_thumb_url": thumb_url,
                "channel_views": channel_views,
            }
        )


class YoutubeChannel(YouTubeItem):
    """represents a single youtube channel"""

    es_path = False
    index_name = "ta_channel"
    yt_base = "https://www.youtube.com/channel/"

    def __init__(self, youtube_id):
        super().__init__(youtube_id)
        self.es_path = f"{self.index_name}/_doc/{youtube_id}"

    def build_json(self, upload=False):
        """get from es or from youtube"""
        self.get_from_es()
        if self.json_data:
            return

        self.get_from_youtube()
        if upload:
            self.upload_to_es()
        return

    def get_from_youtube(self):
        """use bs4 to scrape channel about page"""
        self.json_data = ChannelScraper(self.youtube_id).get_json()
        self.get_channel_art()

    def get_channel_art(self):
        """download channel art for new channels"""
        channel_id = self.youtube_id
        channel_thumb = self.json_data["channel_thumb_url"]
        channel_banner = self.json_data["channel_banner_url"]
        ThumbManager().download_chan(
            [(channel_id, channel_thumb, channel_banner)]
        )

    def sync_to_videos(self):
        """sync new channel_dict to all videos of channel"""
        # add ingest pipeline
        processors = []
        for field, value in self.json_data.items():
            line = {"set": {"field": "channel." + field, "value": value}}
            processors.append(line)
        data = {"description": self.youtube_id, "processors": processors}
        ingest_path = f"_ingest/pipeline/{self.youtube_id}"
        _, _ = ElasticWrap(ingest_path).put(data)
        # apply pipeline
        data = {"query": {"match": {"channel.channel_id": self.youtube_id}}}
        update_path = f"ta_video/_update_by_query?pipeline={self.youtube_id}"
        _, _ = ElasticWrap(update_path).post(data)

    def get_folder_path(self):
        """get folder where media files get stored"""
        channel_name = self.json_data["channel_name"]
        folder_name = clean_string(channel_name)
        folder_path = os.path.join(self.app_conf["videos"], folder_name)
        return folder_path

    def delete_es_videos(self):
        """delete all channel documents from elasticsearch"""
        data = {
            "query": {
                "term": {"channel.channel_id": {"value": self.youtube_id}}
            }
        }
        _, _ = ElasticWrap("ta_video/_delete_by_query").post(data)

    def delete_playlists(self):
        """delete all indexed playlist from es"""
        all_playlists = self.get_indexed_playlists()
        for playlist in all_playlists:
            playlist_id = playlist["playlist_id"]
            YoutubePlaylist(playlist_id).delete_metadata()

    def delete_channel(self):
        """delete channel and all videos"""
        print(f"{self.youtube_id}: delete channel")
        self.get_from_es()
        folder_path = self.get_folder_path()
        print(f"{self.youtube_id}: delete all media files")
        try:
            all_videos = os.listdir(folder_path)
            for video in all_videos:
                video_path = os.path.join(folder_path, video)
                os.remove(video_path)
            os.rmdir(folder_path)
        except FileNotFoundError:
            print(f"no videos found for {folder_path}")

        print(f"{self.youtube_id}: delete indexed playlists")
        self.delete_playlists()
        print(f"{self.youtube_id}: delete indexed videos")
        self.delete_es_videos()
        self.del_in_es()

    def get_all_playlists(self):
        """get all playlists owned by this channel"""
        url = (
            f"https://www.youtube.com/channel/{self.youtube_id}"
            + "/playlists?view=1&sort=dd&shelf_id=0"
        )
        obs = {
            "quiet": True,
            "skip_download": True,
            "extract_flat": True,
        }
        playlists = yt_dlp.YoutubeDL(obs).extract_info(url)
        all_entries = [(i["id"], i["title"]) for i in playlists["entries"]]

        return all_entries

    def get_indexed_playlists(self):
        """get all indexed playlists from channel"""
        data = {
            "query": {
                "term": {"playlist_channel_id": {"value": self.youtube_id}}
            },
            "sort": [{"playlist_channel.keyword": {"order": "desc"}}],
        }
        all_playlists = IndexPaginate("ta_playlist", data).get_results()
        return all_playlists


class YoutubePlaylist(YouTubeItem):
    """represents a single youtube playlist"""

    es_path = False
    index_name = "ta_playlist"
    yt_obs = {
        "default_search": "ytsearch",
        "quiet": True,
        "skip_download": True,
        "extract_flat": True,
    }
    yt_base = "https://www.youtube.com/playlist?list="

    def __init__(self, youtube_id):
        super().__init__(youtube_id)
        self.es_path = f"{self.index_name}/_doc/{youtube_id}"
        self.all_members = False
        self.nav = False
        self.all_youtube_ids = []

    def build_json(self, scrape=False):
        """collection to create json_data"""
        if not scrape:
            self.get_from_es()

        if scrape or not self.json_data:
            self.get_from_youtube()
            self.process_youtube_meta()
            self.get_entries()
            self.json_data["playlist_entries"] = self.all_members
            self.get_playlist_art()

    def process_youtube_meta(self):
        """extract relevant fields from youtube"""
        self.json_data = {
            "playlist_id": self.youtube_id,
            "playlist_active": True,
            "playlist_subscribed": False,
            "playlist_name": self.youtube_meta["title"],
            "playlist_channel": self.youtube_meta["channel"],
            "playlist_channel_id": self.youtube_meta["channel_id"],
            "playlist_thumbnail": self.youtube_meta["thumbnails"][-1]["url"],
            "playlist_description": self.youtube_meta["description"] or False,
            "playlist_last_refresh": int(datetime.now().strftime("%s")),
        }

    def get_entries(self, playlistend=False):
        """get all videos in playlist"""
        if playlistend:
            # implement playlist end
            print(playlistend)
        all_members = []
        for idx, entry in enumerate(self.youtube_meta["entries"]):
            if self.all_youtube_ids:
                downloaded = entry["id"] in self.all_youtube_ids
            else:
                downloaded = False
            if not entry["uploader"]:
                continue
            to_append = {
                "youtube_id": entry["id"],
                "title": entry["title"],
                "uploader": entry["uploader"],
                "idx": idx,
                "downloaded": downloaded,
            }
            all_members.append(to_append)

        self.all_members = all_members

    @staticmethod
    def get_playlist_art():
        """download artwork of playlist"""
        thumbnails = ThumbManager()
        missing_playlists = thumbnails.get_missing_playlists()
        thumbnails.download_playlist(missing_playlists)

    def add_vids_to_playlist(self):
        """sync the playlist id to videos"""
        script = (
            'if (!ctx._source.containsKey("playlist")) '
            + "{ctx._source.playlist = [params.playlist]} "
            + "else if (!ctx._source.playlist.contains(params.playlist)) "
            + "{ctx._source.playlist.add(params.playlist)} "
            + "else {ctx.op = 'none'}"
        )

        bulk_list = []
        for entry in self.json_data["playlist_entries"]:
            video_id = entry["youtube_id"]
            action = {"update": {"_id": video_id, "_index": "ta_video"}}
            source = {
                "script": {
                    "source": script,
                    "lang": "painless",
                    "params": {"playlist": self.youtube_id},
                }
            }
            bulk_list.append(json.dumps(action))
            bulk_list.append(json.dumps(source))

        # add last newline
        bulk_list.append("\n")
        query_str = "\n".join(bulk_list)

        ElasticWrap("_bulk").post(query_str, ndjson=True)

    def update_playlist(self):
        """update metadata for playlist with data from YouTube"""
        self.get_from_es()
        subscribed = self.json_data["playlist_subscribed"]
        self.get_from_youtube()
        if not self.json_data:
            # return false to deactivate
            return False

        self.json_data["playlist_subscribed"] = subscribed
        self.upload_to_es()
        return True

    def build_nav(self, youtube_id):
        """find next and previous in playlist of a given youtube_id"""
        all_entries_available = self.json_data["playlist_entries"]
        all_entries = [i for i in all_entries_available if i["downloaded"]]
        current = [i for i in all_entries if i["youtube_id"] == youtube_id]
        # stop if not found or playlist of 1
        if not current or not len(all_entries) > 1:
            return

        current_idx = all_entries.index(current[0])
        if current_idx == 0:
            previous_item = False
        else:
            previous_item = all_entries[current_idx - 1]
            prev_thumb = ThumbManager().vid_thumb_path(
                previous_item["youtube_id"]
            )
            previous_item["vid_thumb"] = prev_thumb

        if current_idx == len(all_entries) - 1:
            next_item = False
        else:
            next_item = all_entries[current_idx + 1]
            next_thumb = ThumbManager().vid_thumb_path(next_item["youtube_id"])
            next_item["vid_thumb"] = next_thumb

        self.nav = {
            "playlist_meta": {
                "current_idx": current[0]["idx"],
                "playlist_id": self.youtube_id,
                "playlist_name": self.json_data["playlist_name"],
                "playlist_channel": self.json_data["playlist_channel"],
            },
            "playlist_previous": previous_item,
            "playlist_next": next_item,
        }
        return

    def delete_metadata(self):
        """delete metadata for playlist"""
        script = (
            "ctx._source.playlist.removeAll("
            + "Collections.singleton(params.playlist)) "
        )
        data = {
            "query": {
                "term": {"playlist.keyword": {"value": self.youtube_id}}
            },
            "script": {
                "source": script,
                "lang": "painless",
                "params": {"playlist": self.youtube_id},
            },
        }
        _, _ = ElasticWrap("ta_video/_update_by_query").post(data)
        self.del_in_es()

    def delete_videos_playlist(self):
        """delete playlist with all videos"""
        print(f"{self.youtube_id}: delete playlist")
        self.get_from_es()
        all_youtube_id = [
            i["youtube_id"]
            for i in self.json_data["playlist_entries"]
            if i["downloaded"]
        ]
        for youtube_id in all_youtube_id:
            YoutubeVideo(youtube_id).delete_media_file()

        self.delete_metadata()


class WatchState:
    """handle watched checkbox for videos and channels"""

    CONFIG = AppConfig().config
    ES_URL = CONFIG["application"]["es_url"]
    ES_AUTH = CONFIG["application"]["es_auth"]
    HEADERS = {"Content-type": "application/json"}

    def __init__(self, youtube_id):
        self.youtube_id = youtube_id
        self.stamp = int(datetime.now().strftime("%s"))

    def mark_as_watched(self):
        """update es with new watched value"""
        url_type = self.dedect_type()
        if url_type == "video":
            self.mark_vid_watched()
        elif url_type == "channel":
            self.mark_channel_watched()
        elif url_type == "playlist":
            self.mark_playlist_watched()

        print(f"marked {self.youtube_id} as watched")

    def mark_as_unwatched(self):
        """revert watched state to false"""
        url_type = self.dedect_type()
        if url_type == "video":
            self.mark_vid_watched(revert=True)

        print(f"revert {self.youtube_id} as unwatched")

    def dedect_type(self):
        """find youtube id type"""
        print(self.youtube_id)
        url_process = UrlListParser(self.youtube_id).process_list()
        url_type = url_process[0]["type"]
        return url_type

    def mark_vid_watched(self, revert=False):
        """change watched status of single video"""
        url = self.ES_URL + "/ta_video/_update/" + self.youtube_id
        data = {
            "doc": {"player": {"watched": True, "watched_date": self.stamp}}
        }
        if revert:
            data["doc"]["player"]["watched"] = False

        payload = json.dumps(data)
        request = requests.post(
            url, data=payload, headers=self.HEADERS, auth=self.ES_AUTH
        )
        if not request.ok:
            print(request.text)
            raise ValueError("failed to mark video as watched")

    def mark_channel_watched(self):
        """change watched status of every video in channel"""
        data = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "term": {
                                "channel.channel_id": {
                                    "value": self.youtube_id
                                }
                            }
                        },
                        {"term": {"player.watched": {"value": False}}},
                    ]
                }
            },
            "script": {
                "source": "ctx._source.player['watched'] = true",
                "lang": "painless",
            },
        }
        payload = json.dumps(data)
        url = f"{self.ES_URL}/ta_video/_update_by_query"
        request = requests.post(
            url, data=payload, headers=self.HEADERS, auth=self.ES_AUTH
        )
        if not request.ok:
            print(request.text)
            raise ValueError("failed mark channel as watched")

    def mark_playlist_watched(self):
        """change watched state of all videos in playlist"""
        data = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "term": {
                                "playlist.keyword": {"value": self.youtube_id}
                            }
                        },
                        {"term": {"player.watched": {"value": False}}},
                    ]
                }
            },
            "script": {
                "source": "ctx._source.player['watched'] = true",
                "lang": "painless",
            },
        }
        payload = json.dumps(data)
        url = f"{self.ES_URL}/ta_video/_update_by_query"
        request = requests.post(
            url, data=payload, headers=self.HEADERS, auth=self.ES_AUTH
        )
        if not request.ok:
            print(request.text)
            raise ValueError("failed mark playlist as watched")


def index_new_video(youtube_id):
    """combined classes to create new video in index"""
    video = YoutubeVideo(youtube_id)
    video.build_json()
    if not video.json_data:
        raise ValueError("failed to get metadata for " + youtube_id)

    video.upload_to_es()
    return video.json_data
