"""
functionality:
- get metadata from youtube for a playlist
- index and update in es
"""

import json
from datetime import datetime

from home.src.download.thumbnails import ThumbManager
from home.src.es.connect import ElasticWrap, IndexPaginate
from home.src.index import channel
from home.src.index.generic import YouTubeItem
from home.src.index.video import YoutubeVideo


class YoutubePlaylist(YouTubeItem):
    """represents a single youtube playlist"""

    es_path = False
    index_name = "ta_playlist"
    yt_obs = {
        "extract_flat": True,
        "allow_playlist_files": True,
    }
    yt_base = "https://www.youtube.com/playlist?list="

    def __init__(self, youtube_id):
        super().__init__(youtube_id)
        self.all_members = False
        self.nav = False

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
            self._ensure_channel()
            ids_found = self.get_local_vids()
            self.get_entries(ids_found)
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
            "playlist_type": "regular",
        }

    def _ensure_channel(self):
        """make sure channel is indexed"""
        channel_id = self.json_data["playlist_channel_id"]
        channel_handler = channel.YoutubeChannel(channel_id)
        channel_handler.build_json(upload=True)

    def get_local_vids(self) -> list[str]:
        """get local video ids from youtube entries"""
        entries = self.youtube_meta["entries"]
        data = {
            "query": {"terms": {"youtube_id": [i["id"] for i in entries]}},
            "_source": ["youtube_id"],
        }
        indexed_vids = IndexPaginate("ta_video", data).get_results()
        ids_found = [i["youtube_id"] for i in indexed_vids]

        return ids_found

    def get_entries(self, ids_found) -> None:
        """get all videos in playlist, match downloaded with ids_found"""
        all_members = []
        for idx, entry in enumerate(self.youtube_meta["entries"]):
            to_append = {
                "youtube_id": entry["id"],
                "title": entry["title"],
                "uploader": entry.get("channel"),
                "idx": idx,
                "downloaded": entry["id"] in ids_found,
            }
            all_members.append(to_append)

        self.all_members = all_members

    def get_playlist_art(self):
        """download artwork of playlist"""
        url = self.json_data["playlist_thumbnail"]
        ThumbManager(self.youtube_id, item_type="playlist").download(url)

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

    def remove_vids_from_playlist(self):
        """remove playlist ids from videos if needed"""
        needed = [i["youtube_id"] for i in self.json_data["playlist_entries"]]
        data = {
            "query": {"match": {"playlist": self.youtube_id}},
            "_source": ["youtube_id"],
        }
        result = IndexPaginate("ta_video", data).get_results()
        to_remove = [
            i["youtube_id"] for i in result if i["youtube_id"] not in needed
        ]
        s = "ctx._source.playlist.removeAll(Collections.singleton(params.rm))"
        for video_id in to_remove:
            query = {
                "script": {
                    "source": s,
                    "lang": "painless",
                    "params": {"rm": self.youtube_id},
                },
                "query": {"match": {"youtube_id": video_id}},
            }
            path = "ta_video/_update_by_query"
            _, status_code = ElasticWrap(path).post(query)
            if status_code == 200:
                print(f"{self.youtube_id}: removed {video_id} from playlist")

    def update_playlist(self, skip_on_empty=False):
        """update metadata for playlist with data from YouTube"""
        self.build_json(scrape=True)
        if not self.json_data:
            # return false to deactivate
            return False

        if skip_on_empty:
            has_item_downloaded = any(
                i["downloaded"] for i in self.json_data["playlist_entries"]
            )
            if not has_item_downloaded:
                return True

        self.upload_to_es()
        self.add_vids_to_playlist()
        self.remove_vids_from_playlist()
        self.get_playlist_art()
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
        self.delete_videos_metadata()
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

    def is_custom_playlist(self):
        self.get_from_es()
        return self.json_data["playlist_type"] == "custom"

    def delete_videos_metadata(self, channel_id=None):
        """delete video metadata for a specific channel"""
        self.get_from_es()
        playlist = self.json_data["playlist_entries"]
        i = 0
        while i < len(playlist):
            video_id = playlist[i]["youtube_id"]
            video = YoutubeVideo(video_id)
            video.get_from_es()
            if (
                channel_id is None
                or video.json_data["channel"]["channel_id"] == channel_id
            ):
                playlist.pop(i)
                self.remove_playlist_from_video(video_id)
                i -= 1
            i += 1
        self.set_playlist_thumbnail()
        self.upload_to_es()

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

    def create(self, name):
        self.json_data = {
            "playlist_id": self.youtube_id,
            "playlist_active": False,
            "playlist_name": name,
            "playlist_last_refresh": int(datetime.now().timestamp()),
            "playlist_entries": [],
            "playlist_type": "custom",
            "playlist_channel": None,
            "playlist_channel_id": None,
            "playlist_description": False,
            "playlist_thumbnail": False,
            "playlist_subscribed": False,
        }
        self.upload_to_es()
        self.get_playlist_art()
        return True

    def add_video_to_playlist(self, video_id):
        self.get_from_es()
        video_metadata = self.get_video_metadata(video_id)
        video_metadata["idx"] = len(self.json_data["playlist_entries"])

        if not self.playlist_entries_contains(video_id):
            self.json_data["playlist_entries"].append(video_metadata)
            self.json_data["playlist_last_refresh"] = int(
                datetime.now().timestamp()
            )
            self.set_playlist_thumbnail()
            self.upload_to_es()
            video = YoutubeVideo(video_id)
            video.get_from_es()
            if "playlist" not in video.json_data:
                video.json_data["playlist"] = []
            video.json_data["playlist"].append(self.youtube_id)
            video.upload_to_es()
        return True

    def remove_playlist_from_video(self, video_id):
        video = YoutubeVideo(video_id)
        video.get_from_es()
        if video.json_data is not None and "playlist" in video.json_data:
            video.json_data["playlist"].remove(self.youtube_id)
            video.upload_to_es()

    def move_video(self, video_id, action, hide_watched=False):
        self.get_from_es()
        video_index = self.get_video_index(video_id)
        playlist = self.json_data["playlist_entries"]
        item = playlist[video_index]
        playlist.pop(video_index)
        if action == "remove":
            self.remove_playlist_from_video(item["youtube_id"])
        else:
            if action == "up":
                while True:
                    video_index = max(0, video_index - 1)
                    if (
                        not hide_watched
                        or video_index == 0
                        or (
                            not self.get_video_is_watched(
                                playlist[video_index]["youtube_id"]
                            )
                        )
                    ):
                        break
            elif action == "down":
                while True:
                    video_index = min(len(playlist), video_index + 1)
                    if (
                        not hide_watched
                        or video_index == len(playlist)
                        or (
                            not self.get_video_is_watched(
                                playlist[video_index - 1]["youtube_id"]
                            )
                        )
                    ):
                        break
            elif action == "top":
                video_index = 0
            else:
                video_index = len(playlist)
            playlist.insert(video_index, item)
        self.json_data["playlist_last_refresh"] = int(
            datetime.now().timestamp()
        )

        for i, item in enumerate(playlist):
            item["idx"] = i

        self.set_playlist_thumbnail()
        self.upload_to_es()

        return True

    def del_video(self, video_id):
        playlist = self.json_data["playlist_entries"]

        i = 0
        while i < len(playlist):
            if video_id == playlist[i]["youtube_id"]:
                playlist.pop(i)
                self.set_playlist_thumbnail()
                i -= 1
            i += 1

    def get_video_index(self, video_id):
        for i, child in enumerate(self.json_data["playlist_entries"]):
            if child["youtube_id"] == video_id:
                return i
        return -1

    def playlist_entries_contains(self, video_id):
        return (
            len(
                list(
                    filter(
                        lambda x: x["youtube_id"] == video_id,
                        self.json_data["playlist_entries"],
                    )
                )
            )
            > 0
        )

    def get_video_is_watched(self, video_id):
        video = YoutubeVideo(video_id)
        video.get_from_es()
        return video.json_data["player"]["watched"]

    def set_playlist_thumbnail(self):
        playlist = self.json_data["playlist_entries"]
        self.json_data["playlist_thumbnail"] = False

        for video in playlist:
            url = ThumbManager(video["youtube_id"]).vid_thumb_path()
            if url is not None:
                self.json_data["playlist_thumbnail"] = url
                break
        self.get_playlist_art()

    def get_video_metadata(self, video_id):
        video = YoutubeVideo(video_id)
        video.get_from_es()
        video_json_data = {
            "youtube_id": video.json_data["youtube_id"],
            "title": video.json_data["title"],
            "uploader": video.json_data["channel"]["channel_name"],
            "idx": 0,
            "downloaded": "date_downloaded" in video.json_data
            and video.json_data["date_downloaded"] > 0,
        }
        return video_json_data
