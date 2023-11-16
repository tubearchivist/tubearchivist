"""
functionality:
- get metadata from youtube for a playlist
- index and update in es
"""

import json
import logging
import uuid
from datetime import datetime

from home.src.download.thumbnails import ThumbManager
from home.src.es.connect import ElasticWrap
from home.src.index.generic import YouTubeItem
from home.src.index.video import YoutubeVideo


class CustomPlaylist(YouTubeItem):
    """represents a single youtube playlist"""

    es_path = False
    index_name = "ta_custom_playlist"
    yt_obs = {
        "extract_flat": True,
        "allow_playlist_files": True,
    }
    yt_base = "https://www.youtube.com/playlist?list="

    def __init__(self, id=None):
        if id is None:
            id = str(uuid.uuid4())
        super().__init__(id)
        self.all_members = False
        self.nav = False
        self.all_youtube_ids = []
    
    def create(self, name):
        self.json_data = {
            "playlist_id": self.youtube_id,
            "playlist_active": True,
            "playlist_name": name,
            "playlist_last_refresh": int(datetime.now().timestamp()),
            "playlist_entries": [],
        }
        
        self.upload_to_es()
        ThumbManager(self.youtube_id, item_type="custom_playlist").download()
        return True

    def build_json(self, scrape=False):
        """collection to create json_data"""
        self.get_from_es()
        if self.json_data:
            subscribed = self.json_data.get("playlist_subscribed")
        else:
            subscribed = False

        if scrape or not self.json_data:
            self.get_from_youtube()
            if not self.youtube_meta:
                self.json_data = False
                return

            self.process_youtube_meta()
            self.get_entries()
            self.json_data["playlist_entries"] = self.all_members
            self.json_data["playlist_subscribed"] = subscribed

    def process_youtube_meta(self):
        """extract relevant fields from youtube"""
        try:
            playlist_thumbnail = self.youtube_meta["thumbnails"][-1]["url"]
        except IndexError:
            print(f"{self.youtube_id}: thumbnail extraction failed")
            playlist_thumbnail = False

        self.json_data = {
            "playlist_id": self.youtube_id,
            "playlist_active": True,
            "playlist_name": self.youtube_meta["title"],
            "playlist_channel": self.youtube_meta["channel"],
            "playlist_channel_id": self.youtube_meta["channel_id"],
            "playlist_thumbnail": playlist_thumbnail,
            "playlist_description": self.youtube_meta["description"] or False,
            "playlist_last_refresh": int(datetime.now().timestamp()),
            "playlist_entries": [],
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
            if not entry["channel"]:
                continue
            to_append = {
                "youtube_id": entry["id"],
                "title": entry["title"],
                "uploader": entry["channel"],
                "idx": idx,
                "downloaded": downloaded,
            }
            all_members.append(to_append)

        self.all_members = all_members

    def get_playlist_art(self):
        """download artwork of playlist"""
        url = self.json_data["playlist_thumbnail"]
        ThumbManager(self.youtube_id, item_type="playlist").download(url)

    def add_video_to_playlist(self, video_id):
        logging.debug("add_video_to_playlist: %s", video_id)
        
        self.get_from_es()
        video_metadata = self.get_video_metadata(video_id)
        
        logging.debug("video %s", video_metadata)
          
        if not self.playlist_entries_contains(video_id):
            self.json_data["playlist_entries"].append(video_metadata)
            self.json_data["playlist_last_refresh"] = int(datetime.now().timestamp())
            self.upload_to_es()
            
        return True
    
    def move_video(self, video_id, action):
        logging.debug("move_video: %s %s", video_id, action)
        
        self.get_from_es()
        
        video_index = self.get_video_index(video_id)
        
        logging.debug("video index %s", video_index)
          
        playlist = self.json_data["playlist_entries"]
        item = playlist[video_index]
        playlist.pop(video_index)
        
        if action != "remove":
            if action == "up":
                video_index = max(0,video_index-1)
            elif action == "down":
                video_index = min(len(playlist),video_index+1)
            elif action == "top":
                video_index = 0
            else:
                video_index = len(playlist)
            
            playlist.insert(video_index, item)
        
        self.json_data["playlist_last_refresh"] = int(datetime.now().timestamp())
        self.upload_to_es()
            
        return True
    
    def get_video_index(self, video_id):
        for i,child in enumerate(self.json_data["playlist_entries"]):
            if child["youtube_id"] == video_id:
                return i
        return -1
            
    def playlist_entries_contains(self, video_id):
         return len(list(filter(lambda x:x["youtube_id"]==video_id, self.json_data["playlist_entries"] ))) > 0
        
    def get_video_metadata(self, video_id):
        video = YoutubeVideo(video_id)
        video.get_from_es()
        return video.json_data
    
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
            prev_id = previous_item["youtube_id"]
            previous_item["vid_thumb"] = ThumbManager(prev_id).vid_thumb_path()

        if current_idx == len(all_entries) - 1:
            next_item = False
        else:
            next_item = all_entries[current_idx + 1]
            next_id = next_item["youtube_id"]
            next_item["vid_thumb"] = ThumbManager(next_id).vid_thumb_path()

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
        
        logging.debug("delete_metadata")
        script = (
            "ctx._source.custom_playlist.removeAll("
            + "Collections.singleton(params.custom_playlist)) "
        )
        data = {
            "query": {
                "term": {"custom_playlist.keyword": {"value": self.youtube_id}}
            },
            "script": {
                "source": script,
                "lang": "painless",
                "params": {"custom_playlist": self.youtube_id},
            },
        }
        _, _ = ElasticWrap("ta_custom_playlist/_update_by_query").post(data)
        self.del_in_es()
        
        ThumbManager(self.youtube_id, item_type="custom_playlist").delete()

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
