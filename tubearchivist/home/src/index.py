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
from time import sleep

import requests
import yt_dlp as youtube_dl
from bs4 import BeautifulSoup
from home.src.config import AppConfig
from home.src.helper import DurationConverter, UrlListParser, clean_string
from home.src.thumbnails import ThumbManager


class YoutubeChannel:
    """represents a single youtube channel"""

    CONFIG = AppConfig().config
    ES_URL = CONFIG["application"]["es_url"]
    ES_AUTH = CONFIG["application"]["es_auth"]
    CACHE_DIR = CONFIG["application"]["cache_dir"]
    VIDEOS = CONFIG["application"]["videos"]

    def __init__(self, channel_id):
        self.channel_id = channel_id
        self.json_data = None
        self.source = None
        self.channel_dict = self.build_channel_dict()

    def build_channel_dict(self, scrape=False):
        """combine the dicts build from extracted json payload"""
        if scrape:
            channel_dict = False
        else:
            channel_dict = self.get_es_channel()
        if not channel_dict:
            print("scrape data from youtube")
            self.scrape_channel()
            channel_dict = self.parse_channel_main()
            channel_dict.update(self.parse_channel_meta())
            self.source = "scraped"
        return channel_dict

    def get_es_channel(self):
        """get from elastic search first if possible"""
        channel_id = self.channel_id
        url = f"{self.ES_URL}/ta_channel/_doc/{channel_id}"
        response = requests.get(url, auth=self.ES_AUTH)
        if response.ok:
            channel_source = response.json()["_source"]
            self.source = "elastic"
            return channel_source
        return False

    def scrape_channel(self):
        """scrape channel page for additional infos"""
        channel_id = self.channel_id
        url = f"https://www.youtube.com/channel/{channel_id}/about?hl=en"
        cookies = {"CONSENT": "YES+xxxxxxxxxxxxxxxxxxxxxxxxxxx"}
        response = requests.get(url, cookies=cookies, auth=self.ES_AUTH)
        if response.ok:
            channel_page = response.text
        else:
            print(f"failed to extract channel info for: {channel_id}")
            raise ConnectionError
        soup = BeautifulSoup(channel_page, "html.parser")
        # load script into json
        all_scripts = soup.find("body").find_all("script")
        for script in all_scripts:
            if "var ytInitialData = " in str(script):
                script_content = str(script)
                break
        # extract payload
        script_content = script_content.split("var ytInitialData = ")[1]
        json_raw = script_content.rstrip(";</script>")
        json_data = json.loads(json_raw)
        # add to self
        self.json_data = json_data

    def parse_channel_main(self):
        """extract maintab values from scraped channel json data"""
        main_tab = self.json_data["header"]["c4TabbedHeaderRenderer"]
        channel_name = main_tab["title"]
        last_refresh = int(datetime.now().strftime("%s"))
        # channel_subs
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
        # banner
        try:
            all_banners = main_tab["banner"]["thumbnails"]
            banner = sorted(all_banners, key=lambda k: k["width"])[-1]["url"]
        except KeyError:
            banner = False
        # build and return dict
        main_channel_dict = {
            "channel_active": True,
            "channel_last_refresh": last_refresh,
            "channel_subs": channel_subs,
            "channel_banner_url": banner,
            "channel_name": channel_name,
            "channel_id": self.channel_id,
        }
        return main_channel_dict

    def parse_channel_meta(self):
        """extract meta tab values from channel payload"""
        # meta tab
        json_data = self.json_data
        meta_tab = json_data["metadata"]["channelMetadataRenderer"]
        description = meta_tab["description"]
        all_thumbs = meta_tab["avatar"]["thumbnails"]
        thumb_url = sorted(all_thumbs, key=lambda k: k["width"])[-1]["url"]
        # stats tab
        renderer = "twoColumnBrowseResultsRenderer"
        all_tabs = json_data["contents"][renderer]["tabs"]
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

        meta_channel_dict = {
            "channel_description": description,
            "channel_thumb_url": thumb_url,
            "channel_views": channel_views,
        }

        return meta_channel_dict

    def get_channel_art(self):
        """download channel art for new channels"""
        channel_id = self.channel_id
        channel_thumb = self.channel_dict["channel_thumb_url"]
        channel_banner = self.channel_dict["channel_banner_url"]
        ThumbManager().download_chan(
            [(channel_id, channel_thumb, channel_banner)]
        )

    def upload_to_es(self):
        """upload channel data to elastic search"""
        url = f"{self.ES_URL}/ta_channel/_doc/{self.channel_id}"
        response = requests.put(url, json=self.channel_dict, auth=self.ES_AUTH)
        print(f"added {self.channel_id} to es")
        if not response.ok:
            print(response.text)
            raise ValueError("failed to add channel to index")

    def sync_to_videos(self):
        """sync new channel_dict to all videos of channel"""
        headers = {"Content-type": "application/json"}
        channel_id = self.channel_id
        # add ingest pipeline
        processors = []
        for field, value in self.channel_dict.items():
            line = {"set": {"field": "channel." + field, "value": value}}
            processors.append(line)
        data = {"description": channel_id, "processors": processors}
        payload = json.dumps(data)
        url = self.ES_URL + "/_ingest/pipeline/" + channel_id
        request = requests.put(
            url, data=payload, headers=headers, auth=self.ES_AUTH
        )
        if not request.ok:
            print(request.text)
        # apply pipeline
        data = {"query": {"match": {"channel.channel_id": channel_id}}}
        payload = json.dumps(data)
        url = self.ES_URL + "/ta_video/_update_by_query?pipeline=" + channel_id
        request = requests.post(
            url, data=payload, headers=headers, auth=self.ES_AUTH
        )
        if not request.ok:
            print(request.text)

    def get_folder_path(self):
        """get folder where media files get stored"""
        channel_name = self.channel_dict["channel_name"]
        folder_name = clean_string(channel_name)
        folder_path = os.path.join(self.VIDEOS, folder_name)
        return folder_path

    def delete_es_videos(self):
        """delete all channel documents from elasticsearch"""
        headers = {"Content-type": "application/json"}
        data = {
            "query": {
                "term": {"channel.channel_id": {"value": self.channel_id}}
            }
        }
        payload = json.dumps(data)
        url = self.ES_URL + "/ta_video/_delete_by_query"
        response = requests.post(
            url, data=payload, headers=headers, auth=self.ES_AUTH
        )
        if not response.ok:
            print(response.text)

    def delete_channel(self):
        """delete channel and all videos"""
        print(f"deleting {self.channel_id} and all matching media files")
        folder_path = self.get_folder_path()
        print("delete all media files")
        try:
            all_videos = os.listdir(folder_path)
            for video in all_videos:
                video_path = os.path.join(folder_path, video)
                os.remove(video_path)
            os.rmdir(folder_path)
        except FileNotFoundError:
            print(f"no videos found for {folder_path}")

        ThumbManager().delete_chan_thumb(self.channel_id)

        print("delete indexed videos")
        self.delete_es_videos()
        url = self.ES_URL + "/ta_channel/_doc/" + self.channel_id
        response = requests.delete(url, auth=self.ES_AUTH)
        if not response.ok:
            print(response.text)

    def get_all_playlists(self):
        """get all playlists owned by this channel"""
        url = (
            f"https://www.youtube.com/channel/{self.channel_id}"
            + "/playlists?view=1&sort=dd&shelf_id=0"
        )
        obs = {
            "quiet": True,
            "skip_download": True,
            "extract_flat": True,
        }
        playlists = youtube_dl.YoutubeDL(obs).extract_info(url)
        all_entries = [(i["id"], i["title"]) for i in playlists["entries"]]

        return all_entries

    def get_indexed_playlists(self):
        """get all indexed playlists from channel"""
        data = {
            "query": {
                "term": {"playlist_channel_id": {"value": self.channel_id}}
            },
            "sort": [{"playlist_channel.keyword": {"order": "desc"}}],
        }
        all_playlists = IndexPaginate("ta_playlist", data).get_results()
        return all_playlists


class YoutubeVideo:
    """represents a single youtube video"""

    CONFIG = AppConfig().config
    ES_URL = CONFIG["application"]["es_url"]
    ES_AUTH = CONFIG["application"]["es_auth"]
    CACHE_DIR = CONFIG["application"]["cache_dir"]
    VIDEOS = CONFIG["application"]["videos"]

    def __init__(self, youtube_id):
        self.youtube_id = youtube_id
        self.channel_id = None
        self.vid_dict = None

    def get_vid_dict(self):
        """wrapper to loop around youtube_dl to retry on failure"""
        print(f"get video data for {self.youtube_id}")
        vid_dict = False
        for i in range(3):
            try:
                vid_dict = self.get_youtubedl_vid_data()
            except KeyError as e:
                print(e)
                sleep((i + 1) ** 2)
                continue
            else:
                break

        self.vid_dict = vid_dict

    def get_youtubedl_vid_data(self):
        """parse youtubedl extract info"""
        youtube_id = self.youtube_id
        obs = {
            "quiet": True,
            "default_search": "ytsearch",
            "skip_download": True,
            "check_formats": "selected",
            "noplaylist": True,
        }
        try:
            vid = youtube_dl.YoutubeDL(obs).extract_info(youtube_id)
        except (
            youtube_dl.utils.ExtractorError,
            youtube_dl.utils.DownloadError,
        ):
            print("failed to get info for " + youtube_id)
            return False
        # extract
        self.channel_id = vid["channel_id"]
        upload_date = vid["upload_date"]
        upload_date_time = datetime.strptime(upload_date, "%Y%m%d")
        published = upload_date_time.strftime("%Y-%m-%d")
        last_refresh = int(datetime.now().strftime("%s"))
        # likes
        try:
            like_count = vid["like_count"]
        except KeyError:
            like_count = 0
        try:
            dislike_count = vid["dislike_count"]
        except KeyError:
            dislike_count = 0
        # build dicts
        stats = {
            "view_count": vid["view_count"],
            "like_count": like_count,
            "dislike_count": dislike_count,
            "average_rating": vid["average_rating"],
        }
        vid_basic = {
            "title": vid["title"],
            "description": vid["description"],
            "category": vid["categories"],
            "vid_thumb_url": vid["thumbnail"],
            "tags": vid["tags"],
            "published": published,
            "stats": stats,
            "vid_last_refresh": last_refresh,
            "date_downloaded": last_refresh,
            "youtube_id": youtube_id,
            "active": True,
            "channel": False,
        }

        return vid_basic

    def add_player(self, missing_vid):
        """add player information for new videos"""
        cache_path = self.CACHE_DIR + "/download/"
        videos = self.VIDEOS

        if missing_vid:
            # coming from scan_filesystem
            channel_name, file_name, _ = missing_vid
            vid_path = os.path.join(videos, channel_name, file_name)
        else:
            # coming from VideoDownload
            all_cached = os.listdir(cache_path)
            for file_cached in all_cached:
                if self.youtube_id in file_cached:
                    vid_path = os.path.join(cache_path, file_cached)
                    break

        duration_handler = DurationConverter()
        duration = duration_handler.get_sec(vid_path)
        duration_str = duration_handler.get_str(duration)
        player = {
            "watched": False,
            "duration": duration,
            "duration_str": duration_str,
        }
        self.vid_dict["player"] = player

    def build_file_path(self, channel_name):
        """build media_url from where file will be located"""
        clean_channel_name = clean_string(channel_name)
        timestamp = self.vid_dict["published"].replace("-", "")
        youtube_id = self.vid_dict["youtube_id"]
        title = self.vid_dict["title"]
        clean_title = clean_string(title)
        filename = f"{timestamp}_{youtube_id}_{clean_title}.mp4"
        media_url = os.path.join(clean_channel_name, filename)
        self.vid_dict["media_url"] = media_url

    def get_es_data(self):
        """get current data from elastic search"""
        url = self.ES_URL + "/ta_video/_doc/" + self.youtube_id
        response = requests.get(url, auth=self.ES_AUTH)
        if not response.ok:
            print(response.text)
        es_vid_dict = json.loads(response.text)
        return es_vid_dict

    def upload_to_es(self):
        """upload video data to elastic search"""
        url = f"{self.ES_URL}/ta_video/_doc/{self.youtube_id}/?refresh=true"
        response = requests.put(url, json=self.vid_dict, auth=self.ES_AUTH)
        if not response.ok:
            print(response.text)
            raise ValueError("failed to add video to index")

    def deactivate(self):
        """deactivate document on extractor error"""
        youtube_id = self.youtube_id
        headers = {"Content-type": "application/json"}
        url = f"{self.ES_URL}/ta_video/_update/{youtube_id}"
        data = {"script": "ctx._source.active = false"}
        json_str = json.dumps(data)
        response = requests.post(
            url, data=json_str, headers=headers, auth=self.ES_AUTH
        )
        print(f"deactivated {youtube_id}")
        if not response.ok:
            print(response.text)

    def delete_media_file(self):
        """delete video file, meta data, thumbnails"""
        # delete media file
        es_vid_dict = self.get_es_data()
        media_url = es_vid_dict["_source"]["media_url"]
        print(f"delete {media_url} from file system")
        to_delete = os.path.join(self.VIDEOS, media_url)
        os.remove(to_delete)
        # delete from index
        url = f"{self.ES_URL}/ta_video/_doc/{self.youtube_id}"
        response = requests.delete(url, auth=self.ES_AUTH)
        if not response.ok:
            print(response.text)
        # delete thumbs from cache
        ThumbManager().delete_vid_thumb(self.youtube_id)


class YoutubePlaylist:
    """represent a single playlist on YouTube"""

    CONFIG = AppConfig().config
    ES_URL = CONFIG["application"]["es_url"]
    ES_AUTH = CONFIG["application"]["es_auth"]

    def __init__(self, playlist_id, all_youtube_ids=False):
        self.playlist_id = playlist_id
        self.stamp = int(datetime.now().strftime("%s"))
        self.all_youtube_ids = all_youtube_ids
        self.playlist_dict = False

    def get_playlist_dict(self, scrape=False):
        """get data from es or youtube"""
        print(f"get playlist with id {self.playlist_id}")

        if scrape:
            playlist_dict = self.get_youtube_playlist()
            if not playlist_dict:
                return False
            playlist_dict["playlist_entries"] = self.get_entries()
        else:
            playlist_dict = self.get_es_playlist()
            if not playlist_dict:
                playlist_dict = self.get_youtube_playlist()
                playlist_dict["playlist_entries"] = self.get_entries()

        self.playlist_dict = playlist_dict
        return True

    def get_youtube_playlist(self):
        """get meta data dict from youtube"""
        url = "https://www.youtube.com/playlist?list=" + self.playlist_id
        obs = {
            "default_search": "ytsearch",
            "quiet": True,
            "skip_download": True,
            "extract_flat": True,
            "playlistend": 0,
        }
        try:
            playlist = youtube_dl.YoutubeDL(obs).extract_info(
                url, download=False
            )
        except (
            youtube_dl.utils.ExtractorError,
            youtube_dl.utils.DownloadError,
        ):
            print("failed to get info for " + self.playlist_id)
            return False

        playlist_es = {
            "playlist_id": self.playlist_id,
            "playlist_active": True,
            "playlist_subscribed": False,
            "playlist_name": playlist["title"],
            "playlist_channel": playlist["channel"],
            "playlist_channel_id": playlist["channel_id"],
            "playlist_thumbnail": playlist["thumbnails"][-1]["url"],
            "playlist_description": playlist["description"] or False,
            "playlist_last_refresh": self.stamp,
        }

        return playlist_es

    def get_es_playlist(self):
        """get indexed data from es"""
        url = f"{self.ES_URL}/ta_playlist/_doc/{self.playlist_id}"
        response = requests.get(url, auth=self.ES_AUTH)
        if response.ok:
            return json.loads(response.text)["_source"]

        return False

    def get_entries(self, playlistend=False):
        """get all videos in playlist"""
        url = "https://www.youtube.com/playlist?list=" + self.playlist_id
        obs = {
            "default_search": "ytsearch",
            "quiet": True,
            "skip_download": True,
            "extract_flat": True,
        }
        if playlistend:
            obs["playlistend"] = playlistend

        try:
            playlist = youtube_dl.YoutubeDL(obs).extract_info(
                url, download=False
            )
        except (
            youtube_dl.utils.ExtractorError,
            youtube_dl.utils.DownloadError,
        ):
            print("failed to get plealist entries for " + self.playlist_id)
            return False

        all_members = []
        for idx, entry in enumerate(playlist["entries"]):
            uploader = entry["uploader"]
            youtube_id = entry["id"]
            if self.all_youtube_ids:
                downloaded = youtube_id in self.all_youtube_ids
            else:
                downloaded = False
            if not uploader:
                continue
            to_append = {
                "youtube_id": youtube_id,
                "title": entry["title"],
                "uploader": uploader,
                "idx": idx,
                "downloaded": downloaded,
            }
            all_members.append(to_append)

        return all_members

    def upload_to_es(self):
        """add playlist to es with its entries"""
        playlist = self.playlist_dict
        url = f"{self.ES_URL}/ta_playlist/_doc/{self.playlist_id}"
        response = requests.put(url, json=playlist, auth=self.ES_AUTH)
        if not response.ok:
            print(response.text)
            raise ValueError("failed to add playlist to index")

    def add_vids_to_playlist(self):
        """sync the playlist id to videos"""
        playlist_dict = self.playlist_dict
        script = (
            'if (!ctx._source.containsKey("playlist")) '
            + "{ctx._source.playlist = [params.playlist]} "
            + "else if (!ctx._source.playlist.contains(params.playlist)) "
            + "{ctx._source.playlist.add(params.playlist)} "
            + "else {ctx.op = 'none'}"
        )

        bulk_list = []
        for entry in playlist_dict["playlist_entries"]:
            youtube_id = entry["youtube_id"]
            action = {"update": {"_id": youtube_id, "_index": "ta_video"}}
            source = {
                "script": {
                    "source": script,
                    "lang": "painless",
                    "params": {"playlist": self.playlist_id},
                }
            }
            bulk_list.append(json.dumps(action))
            bulk_list.append(json.dumps(source))

        # add last newline
        bulk_list.append("\n")
        query_str = "\n".join(bulk_list)
        headers = {"Content-type": "application/x-ndjson"}
        url = self.ES_URL + "/_bulk"
        response = requests.post(
            url, data=query_str, headers=headers, auth=self.ES_AUTH
        )
        if not response.ok:
            print(response.text)

    def update_playlist(self):
        """update metadata for playlist with data from YouTube"""
        subscribed = self.get_es_playlist()["playlist_subscribed"]
        self.get_playlist_dict(scrape=True)
        if not self.playlist_dict:
            # return false to deactivate
            return False

        self.playlist_dict["playlist_subscribed"] = subscribed
        self.upload_to_es()
        return self.playlist_dict

    def build_nav(self, youtube_id):
        """find next and previous in playlist of a given youtube_id"""
        all_entries_available = self.playlist_dict["playlist_entries"]
        all_entries = [i for i in all_entries_available if i["downloaded"]]
        current = [i for i in all_entries if i["youtube_id"] == youtube_id]
        # stop if not found or playlist of 1
        if not current or not len(all_entries) > 1:
            return False

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

        nav = {
            "playlist_meta": {
                "current_idx": current[0]["idx"],
                "playlist_id": self.playlist_id,
                "playlist_name": self.playlist_dict["playlist_name"],
                "playlist_channel": self.playlist_dict["playlist_channel"],
            },
            "playlist_previous": previous_item,
            "playlist_next": next_item,
        }
        return nav

    def delete_metadata(self):
        """delete metadata for playlist"""
        script = (
            "ctx._source.playlist.removeAll("
            + "Collections.singleton(params.playlist)) "
        )
        data = {
            "query": {
                "term": {"playlist.keyword": {"value": self.playlist_id}}
            },
            "script": {
                "source": script,
                "lang": "painless",
                "params": {"playlist": self.playlist_id},
            },
        }
        payload = json.dumps(data)
        url = f"{self.ES_URL}/ta_video/_update_by_query"
        headers = {"Content-type": "application/json"}
        response = requests.post(
            url, data=payload, headers=headers, auth=self.ES_AUTH
        )
        if not response.ok:
            print(response.text)

        self.delete_playlist()

    def delete_videos_playlist(self):
        """delete playlist with all videos"""
        print(f"delete playlist {self.playlist_id} with all videos")
        self.get_playlist_dict()
        all_youtube_id = [
            i["youtube_id"]
            for i in self.playlist_dict["playlist_entries"]
            if i["downloaded"]
        ]
        for youtube_id in all_youtube_id:
            YoutubeVideo(youtube_id).delete_media_file()

        self.delete_playlist()

    def delete_playlist(self):
        """delete only playlist document"""
        url = f"{self.ES_URL}/ta_playlist/_doc/{self.playlist_id}"
        response = requests.delete(url, auth=self.ES_AUTH)
        if not response.ok:
            print(response.text)

    def deactivate(self):
        """deactivate document on extractor error"""
        headers = {"Content-type": "application/json"}
        url = f"{self.ES_URL}/ta_playlist/_update/{self.playlist_id}"
        data = {"script": "ctx._source.playlist_active = false"}
        json_str = json.dumps(data)
        response = requests.post(
            url, data=json_str, headers=headers, auth=self.ES_AUTH
        )
        print(f"deactivated {self.playlist_id}")
        if not response.ok:
            print(response.text)


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


class IndexPaginate:
    """use search_after to go through whole index"""

    CONFIG = AppConfig().config
    ES_URL = CONFIG["application"]["es_url"]
    ES_AUTH = CONFIG["application"]["es_auth"]
    HEADERS = {"Content-type": "application/json"}
    DEFAULT_SIZE = 500

    def __init__(self, index_name, data, size=False):
        self.index_name = index_name
        self.data = data
        self.pit_id = False
        self.size = size

    def get_results(self):
        """get all results"""
        self.get_pit()
        self.validate_data()
        all_results = self.run_loop()
        self.clean_pit()
        return all_results

    def get_pit(self):
        """get pit for index"""
        url = f"{self.ES_URL}/{self.index_name}/_pit?keep_alive=10m"
        response = requests.post(url, auth=self.ES_AUTH)
        json_data = json.loads(response.text)

        self.pit_id = json_data["id"]

    def validate_data(self):
        """add pit and size to data"""
        if "sort" not in self.data.keys():
            print(self.data)
            raise ValueError("missing sort key in data")

        size = self.size or self.DEFAULT_SIZE

        self.data["size"] = size
        self.data["pit"] = {"id": self.pit_id, "keep_alive": "10m"}

    def run_loop(self):
        """loop through results until last hit"""
        query_str = json.dumps(self.data)
        url = self.ES_URL + "/_search"

        all_results = []
        while True:
            response = requests.get(
                url, data=query_str, headers=self.HEADERS, auth=self.ES_AUTH
            )
            json_data = json.loads(response.text)
            all_hits = json_data["hits"]["hits"]
            if all_hits:
                for hit in all_hits:
                    source = hit["_source"]
                    search_after = hit["sort"]
                    all_results.append(source)
                # update search_after with last hit data
                self.data["search_after"] = search_after
                query_str = json.dumps(self.data)
            else:
                break

        return all_results

    def clean_pit(self):
        """delete pit from elastic search"""
        query_str = json.dumps({"id": self.pit_id})
        requests.delete(
            self.ES_URL + "/_pit",
            data=query_str,
            headers=self.HEADERS,
            auth=self.ES_AUTH,
        )


def index_new_video(youtube_id, missing_vid=False):
    """combine video and channel classes for new video index"""
    vid_handler = YoutubeVideo(youtube_id)
    vid_handler.get_vid_dict()
    if not vid_handler.vid_dict:
        raise ValueError("failed to get metadata for " + youtube_id)

    channel_handler = YoutubeChannel(vid_handler.channel_id)
    # add filepath to vid_dict
    channel_name = channel_handler.channel_dict["channel_name"]
    vid_handler.build_file_path(channel_name)
    # add channel and player to video
    vid_handler.add_player(missing_vid)
    vid_handler.vid_dict["channel"] = channel_handler.channel_dict
    # add new channel to es
    if channel_handler.source == "scraped":
        channel_handler.channel_dict["channel_subscribed"] = False
        channel_handler.upload_to_es()
        channel_handler.get_channel_art()
    # upload video to es
    vid_handler.upload_to_es()
    # return vid_dict for further processing
    return vid_handler.vid_dict
