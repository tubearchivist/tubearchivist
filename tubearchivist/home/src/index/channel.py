"""
functionality:
- get metadata from youtube for a channel
- index and update in es
"""

import json
import os
import re
from datetime import datetime

import requests
import yt_dlp
from bs4 import BeautifulSoup
from home.src.download import queue  # partial import
from home.src.download.thumbnails import ThumbManager
from home.src.es.connect import ElasticWrap, IndexPaginate
from home.src.index.generic import YouTubeItem
from home.src.index.playlist import YoutubePlaylist
from home.src.ta.helper import clean_string, requests_headers
from home.src.ta.ta_redis import RedisArchivist


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
        response = requests.get(
            url, cookies=cookies, headers=requests_headers()
        )
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
        self.all_playlists = False

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
        if len(folder_name) <= 3:
            # fall back to channel id
            folder_name = self.json_data["channel_id"]
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

    def index_channel_playlists(self):
        """add all playlists of channel to index"""
        print(f"{self.youtube_id}: index all playlists")
        self.get_from_es()
        channel_name = self.json_data["channel_name"]
        mess_dict = {
            "status": "message:playlistscan",
            "level": "info",
            "title": "Looking for playlists",
            "message": f"{channel_name}: Scanning channel in progress",
        }
        RedisArchivist().set_message("message:playlistscan", mess_dict)
        self.get_all_playlists()
        if not self.all_playlists:
            print(f"{self.youtube_id}: no playlists found.")
            return

        all_youtube_ids = self.get_all_video_ids()
        for idx, playlist in enumerate(self.all_playlists):
            self._notify_single_playlist(idx, playlist)
            self._index_single_playlist(playlist, all_youtube_ids)

    def _notify_single_playlist(self, idx, playlist):
        """send notification"""
        channel_name = self.json_data["channel_name"]
        mess_dict = {
            "status": "message:playlistscan",
            "level": "info",
            "title": f"{channel_name}: Scanning channel for playlists",
            "message": f"Progress: {idx + 1}/{len(self.all_playlists)}",
        }
        RedisArchivist().set_message("message:playlistscan", mess_dict)
        print("add playlist: " + playlist[1])

    @staticmethod
    def _index_single_playlist(playlist, all_youtube_ids):
        """add single playlist if needed"""
        playlist = YoutubePlaylist(playlist[0])
        playlist.all_youtube_ids = all_youtube_ids
        playlist.build_json()
        if not playlist.json_data:
            return

        entries = playlist.json_data["playlist_entries"]
        downloaded = [i for i in entries if i["downloaded"]]
        if not downloaded:
            return

        playlist.upload_to_es()
        playlist.add_vids_to_playlist()
        playlist.get_playlist_art()

    @staticmethod
    def get_all_video_ids():
        """match all playlists with videos"""
        handler = queue.PendingList()
        handler.get_download()
        handler.get_indexed()
        all_youtube_ids = [i["youtube_id"] for i in handler.all_videos]

        return all_youtube_ids

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
        self.all_playlists = all_entries

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

    def get_overwrites(self):
        """get all per channel overwrites"""
        return self.json_data.get("channel_overwrites", False)

    def set_overwrites(self, overwrites):
        """set per channel overwrites"""
        valid_keys = [
            "download_format",
            "autodelete_days",
            "index_playlists",
            "integrate_sponsorblock",
        ]

        to_write = self.json_data.get("channel_overwrites", {})
        for key, value in overwrites.items():
            if key not in valid_keys:
                raise ValueError(f"invalid overwrite key: {key}")
            if value in [0, "0"]:
                del to_write[key]
                continue
            if value == "1":
                to_write[key] = True
                continue
            if value:
                to_write.update({key: value})

        self.json_data["channel_overwrites"] = to_write


def channel_overwrites(channel_id, overwrites):
    """collection to overwrite settings per channel"""
    channel = YoutubeChannel(channel_id)
    channel.build_json()
    channel.set_overwrites(overwrites)
    channel.upload_to_es()
    channel.sync_to_videos()
