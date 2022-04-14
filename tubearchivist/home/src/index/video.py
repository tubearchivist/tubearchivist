"""
functionality:
- get metadata from youtube for a video
- index and update in es
"""

import json
import os
from datetime import datetime

import requests
from django.conf import settings
from home.src.download.thumbnails import ThumbManager
from home.src.es.connect import ElasticWrap
from home.src.index import channel as ta_channel
from home.src.index.generic import YouTubeItem
from home.src.ta.helper import (
    DurationConverter,
    clean_string,
    randomizor,
    requests_headers,
)
from home.src.ta.ta_redis import RedisArchivist
from ryd_client import ryd_client


class YoutubeSubtitle:
    """handle video subtitle functionality"""

    def __init__(self, video):
        self.video = video
        self.languages = False

    def _sub_conf_parse(self):
        """add additional conf values to self"""
        languages_raw = self.video.config["downloads"]["subtitle"]
        if languages_raw:
            self.languages = [i.strip() for i in languages_raw.split(",")]

    def get_subtitles(self):
        """check what to do"""
        self._sub_conf_parse()
        if not self.languages:
            # no subtitles
            return False

        relevant_subtitles = []
        for lang in self.languages:
            user_sub = self._get_user_subtitles(lang)
            if user_sub:
                relevant_subtitles.append(user_sub)
                continue

            if self.video.config["downloads"]["subtitle_source"] == "auto":
                auto_cap = self._get_auto_caption(lang)
                if auto_cap:
                    relevant_subtitles.append(auto_cap)

        return relevant_subtitles

    def _get_auto_caption(self, lang):
        """get auto_caption subtitles"""
        print(f"{self.video.youtube_id}-{lang}: get auto generated subtitles")
        all_subtitles = self.video.youtube_meta.get("automatic_captions")

        if not all_subtitles:
            return False

        video_media_url = self.video.json_data["media_url"]
        media_url = video_media_url.replace(".mp4", f"-{lang}.vtt")
        all_formats = all_subtitles.get(lang)
        if not all_formats:
            return False

        subtitle = [i for i in all_formats if i["ext"] == "json3"][0]
        subtitle.update(
            {"lang": lang, "source": "auto", "media_url": media_url}
        )

        return subtitle

    def _normalize_lang(self):
        """normalize country specific language keys"""
        all_subtitles = self.video.youtube_meta.get("subtitles")
        if not all_subtitles:
            return False

        all_keys = list(all_subtitles.keys())
        for key in all_keys:
            lang = key.split("-")[0]
            old = all_subtitles.pop(key)
            if lang == "live_chat":
                continue
            all_subtitles[lang] = old

        return all_subtitles

    def _get_user_subtitles(self, lang):
        """get subtitles uploaded from channel owner"""
        print(f"{self.video.youtube_id}-{lang}: get user uploaded subtitles")
        all_subtitles = self._normalize_lang()
        if not all_subtitles:
            return False

        video_media_url = self.video.json_data["media_url"]
        media_url = video_media_url.replace(".mp4", f"-{lang}.vtt")
        all_formats = all_subtitles.get(lang)
        if not all_formats:
            # no user subtitles found
            return False

        subtitle = [i for i in all_formats if i["ext"] == "json3"][0]
        subtitle.update(
            {"lang": lang, "source": "user", "media_url": media_url}
        )

        return subtitle

    def download_subtitles(self, relevant_subtitles):
        """download subtitle files to archive"""
        videos_base = self.video.config["application"]["videos"]
        for subtitle in relevant_subtitles:
            dest_path = os.path.join(videos_base, subtitle["media_url"])
            source = subtitle["source"]
            lang = subtitle.get("lang")
            response = requests.get(
                subtitle["url"], headers=requests_headers()
            )
            if not response.ok:
                print(f"{self.video.youtube_id}: failed to download subtitle")
                print(response.text)
                continue

            parser = SubtitleParser(response.text, lang, source)
            parser.process()
            subtitle_str = parser.get_subtitle_str()
            self._write_subtitle_file(dest_path, subtitle_str)
            if self.video.config["downloads"]["subtitle_index"]:
                query_str = parser.create_bulk_import(self.video, source)
                self._index_subtitle(query_str)

    @staticmethod
    def _write_subtitle_file(dest_path, subtitle_str):
        """write subtitle file to disk"""
        # create folder here for first video of channel
        os.makedirs(os.path.split(dest_path)[0], exist_ok=True)
        with open(dest_path, "w", encoding="utf-8") as subfile:
            subfile.write(subtitle_str)

    @staticmethod
    def _index_subtitle(query_str):
        """send subtitle to es for indexing"""
        _, _ = ElasticWrap("_bulk").post(data=query_str, ndjson=True)


class SubtitleParser:
    """parse subtitle str from youtube"""

    def __init__(self, subtitle_str, lang, source):
        self.subtitle_raw = json.loads(subtitle_str)
        self.lang = lang
        self.source = source
        self.all_cues = False

    def process(self):
        """extract relevant que data"""
        all_events = self.subtitle_raw.get("events")
        if self.source == "auto":
            all_events = self._flat_auto_caption(all_events)

        self.all_cues = []
        for idx, event in enumerate(all_events):
            if "dDurationMs" not in event:
                # some events won't have a duration
                print(f"failed to parse event without duration: {event}")
                continue

            cue = {
                "start": self._ms_conv(event["tStartMs"]),
                "end": self._ms_conv(event["tStartMs"] + event["dDurationMs"]),
                "text": "".join([i.get("utf8") for i in event["segs"]]),
                "idx": idx + 1,
            }
            self.all_cues.append(cue)

    @staticmethod
    def _flat_auto_caption(all_events):
        """flatten autocaption segments"""
        flatten = []
        for event in all_events:
            if "segs" not in event.keys():
                continue
            text = "".join([i.get("utf8") for i in event.get("segs")])
            if not text.strip():
                continue

            if flatten:
                # fix overlapping retiming issue
                last_end = flatten[-1]["tStartMs"] + flatten[-1]["dDurationMs"]
                if event["tStartMs"] < last_end:
                    joined = flatten[-1]["segs"][0]["utf8"] + "\n" + text
                    flatten[-1]["segs"][0]["utf8"] = joined
                    continue

            event.update({"segs": [{"utf8": text}]})
            flatten.append(event)

        return flatten

    @staticmethod
    def _ms_conv(ms):
        """convert ms to timestamp"""
        hours = str((ms // (1000 * 60 * 60)) % 24).zfill(2)
        minutes = str((ms // (1000 * 60)) % 60).zfill(2)
        secs = str((ms // 1000) % 60).zfill(2)
        millis = str(ms % 1000).zfill(3)

        return f"{hours}:{minutes}:{secs}.{millis}"

    def get_subtitle_str(self):
        """create vtt text str from cues"""
        subtitle_str = f"WEBVTT\nKind: captions\nLanguage: {self.lang}"

        for cue in self.all_cues:
            stamp = f"{cue.get('start')} --> {cue.get('end')}"
            cue_text = f"\n\n{cue.get('idx')}\n{stamp}\n{cue.get('text')}"
            subtitle_str = subtitle_str + cue_text

        return subtitle_str

    def create_bulk_import(self, video, source):
        """subtitle lines for es import"""
        documents = self._create_documents(video, source)
        bulk_list = []

        for document in documents:
            document_id = document.get("subtitle_fragment_id")
            action = {"index": {"_index": "ta_subtitle", "_id": document_id}}
            bulk_list.append(json.dumps(action))
            bulk_list.append(json.dumps(document))

        bulk_list.append("\n")
        query_str = "\n".join(bulk_list)

        return query_str

    def _create_documents(self, video, source):
        """process documents"""
        documents = self._chunk_list(video.youtube_id)
        channel = video.json_data.get("channel")
        meta_dict = {
            "youtube_id": video.youtube_id,
            "title": video.json_data.get("title"),
            "subtitle_channel": channel.get("channel_name"),
            "subtitle_channel_id": channel.get("channel_id"),
            "subtitle_last_refresh": int(datetime.now().strftime("%s")),
            "subtitle_lang": self.lang,
            "subtitle_source": source,
        }

        _ = [i.update(meta_dict) for i in documents]

        return documents

    def _chunk_list(self, youtube_id):
        """join cues for bulk import"""
        chunk_list = []

        chunk = {}
        for cue in self.all_cues:
            if chunk:
                text = f"{chunk.get('subtitle_line')} {cue.get('text')}\n"
                chunk["subtitle_line"] = text
            else:
                idx = len(chunk_list) + 1
                chunk = {
                    "subtitle_index": idx,
                    "subtitle_line": cue.get("text"),
                    "subtitle_start": cue.get("start"),
                }

            chunk["subtitle_fragment_id"] = f"{youtube_id}-{self.lang}-{idx}"

            if cue["idx"] % 5 == 0:
                chunk["subtitle_end"] = cue.get("end")
                chunk_list.append(chunk)
                chunk = {}

        return chunk_list


class SponsorBlock:
    """handle sponsor block integration"""

    API = "https://sponsor.ajay.app/api"

    def __init__(self, user_id=False):
        self.user_id = user_id
        self.user_agent = f"{settings.TA_UPSTREAM} {settings.TA_VERSION}"
        self.last_refresh = int(datetime.now().strftime("%s"))

    def get_sb_id(self):
        """get sponsorblock userid or generate if needed"""
        if not self.user_id:
            print("missing request user id")
            raise ValueError

        key = f"{self.user_id}:id_sponsorblock"
        sb_id = RedisArchivist().get_message(key)
        if not sb_id["status"]:
            sb_id = {"status": randomizor(32)}
            RedisArchivist().set_message(key, sb_id, expire=False)

        return sb_id

    def get_timestamps(self, youtube_id):
        """get timestamps from the API"""
        url = f"{self.API}/skipSegments?videoID={youtube_id}"
        headers = {"User-Agent": self.user_agent}
        print(f"{youtube_id}: get sponsorblock timestamps")
        response = requests.get(url, headers=headers)
        if not response.ok:
            print(f"{youtube_id}: sponsorblock failed: {response.text}")
            sponsor_dict = {
                "last_refresh": self.last_refresh,
                "is_enabled": True,
                "segments": [],
            }
        else:
            all_segments = response.json()
            sponsor_dict = self._get_sponsor_dict(all_segments)

        return sponsor_dict

    def _get_sponsor_dict(self, all_segments):
        """format and process response"""
        has_unlocked = False
        cleaned_segments = []
        for segment in all_segments:
            if not segment["locked"]:
                has_unlocked = True
            del segment["userID"]
            del segment["description"]
            cleaned_segments.append(segment)

        sponsor_dict = {
            "last_refresh": self.last_refresh,
            "has_unlocked": has_unlocked,
            "is_enabled": True,
            "segments": cleaned_segments,
        }
        return sponsor_dict

    def post_timestamps(self, youtube_id, start_time, end_time):
        """post timestamps to api"""
        user_id = self.get_sb_id().get("status")
        data = {
            "videoID": youtube_id,
            "startTime": start_time,
            "endTime": end_time,
            "category": "sponsor",
            "userID": user_id,
            "userAgent": self.user_agent,
        }
        url = f"{self.API}/skipSegments?videoID={youtube_id}"
        print(f"post: {data}")
        print(f"to: {url}")

        return {"success": True}, 200

    def vote_on_segment(self, uuid, vote):
        """send vote on existing segment"""
        user_id = self.get_sb_id().get("status")
        data = {
            "UUID": uuid,
            "userID": user_id,
            "type": vote,
        }
        url = f"{self.API}/api/voteOnSponsorTime"
        print(f"post: {data}")
        print(f"to: {url}")

        return {"success": True}, 200


class YoutubeVideo(YouTubeItem, YoutubeSubtitle):
    """represents a single youtube video"""

    es_path = False
    index_name = "ta_video"
    yt_base = "https://www.youtube.com/watch?v="

    def __init__(self, youtube_id, video_overwrites=False):
        super().__init__(youtube_id)
        self.channel_id = False
        self.video_overwrites = video_overwrites
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

        if self._check_get_sb():
            self._get_sponsorblock()

        return

    def _check_get_sb(self):
        """check if need to run sponsor block"""
        integrate = False
        if self.config["downloads"]["integrate_sponsorblock"]:
            integrate = True

        if self.video_overwrites:
            single_overwrite = self.video_overwrites.get(self.youtube_id)
            if not single_overwrite:
                return integrate

            integrate = single_overwrite.get("integrate_sponsorblock", False)

        return integrate

    def _process_youtube_meta(self):
        """extract relevant fields from youtube"""
        # extract
        self.channel_id = self.youtube_meta["channel_id"]
        upload_date = self.youtube_meta["upload_date"]
        upload_date_time = datetime.strptime(upload_date, "%Y%m%d")
        published = upload_date_time.strftime("%Y-%m-%d")
        last_refresh = int(datetime.now().strftime("%s"))
        base64_blur = ThumbManager().get_base64_blur(self.youtube_id)
        # build json_data basics
        self.json_data = {
            "title": self.youtube_meta["title"],
            "description": self.youtube_meta["description"],
            "category": self.youtube_meta["categories"],
            "vid_thumb_url": self.youtube_meta["thumbnail"],
            "vid_thumb_base64": base64_blur,
            "tags": self.youtube_meta["tags"],
            "published": published,
            "vid_last_refresh": last_refresh,
            "date_downloaded": last_refresh,
            "youtube_id": self.youtube_id,
            "active": True,
        }

    def _add_channel(self):
        """add channel dict to video json_data"""
        channel = ta_channel.YoutubeChannel(self.channel_id)
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

        raise FileNotFoundError

    def add_player(self):
        """add player information for new videos"""
        try:
            # when indexing from download task
            vid_path = self.build_dl_cache_path()
        except FileNotFoundError as err:
            # when reindexing needs to handle title rename
            channel = os.path.split(self.json_data["media_url"])[0]
            channel_dir = os.path.join(self.app_conf["videos"], channel)
            all_files = os.listdir(channel_dir)
            for file in all_files:
                if self.youtube_id in file and file.endswith(".mp4"):
                    vid_path = os.path.join(channel_dir, file)
                    break
            else:
                raise FileNotFoundError("could not find video file") from err

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
        if len(clean_channel_name) <= 3:
            # fall back to channel id
            clean_channel_name = self.json_data["channel"]["channel_id"]

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
        to_del = [self.json_data.get("media_url")]

        all_subtitles = self.json_data.get("subtitles")
        if all_subtitles:
            to_del = to_del + [i.get("media_url") for i in all_subtitles]

        for media_url in to_del:
            file_path = os.path.join(video_base, media_url)
            try:
                os.remove(file_path)
            except FileNotFoundError:
                print(f"{self.youtube_id}: failed {media_url}, continue.")

        self.del_in_es()
        self.delete_subtitles()

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

    def _get_sponsorblock(self):
        """get optional sponsorblock timestamps from sponsor.ajay.app"""
        sponsorblock = SponsorBlock().get_timestamps(self.youtube_id)
        if sponsorblock:
            self.json_data["sponsorblock"] = sponsorblock

    def check_subtitles(self):
        """optionally add subtitles"""
        handler = YoutubeSubtitle(self)
        subtitles = handler.get_subtitles()
        if subtitles:
            self.json_data["subtitles"] = subtitles
            handler.download_subtitles(relevant_subtitles=subtitles)

    def delete_subtitles(self):
        """delete indexed subtitles"""
        path = "ta_subtitle/_delete_by_query?refresh=true"
        data = {"query": {"term": {"youtube_id": {"value": self.youtube_id}}}}
        _, _ = ElasticWrap(path).post(data=data)


def index_new_video(youtube_id, video_overwrites=False):
    """combined classes to create new video in index"""
    video = YoutubeVideo(youtube_id, video_overwrites=video_overwrites)
    video.build_json()
    if not video.json_data:
        raise ValueError("failed to get metadata for " + youtube_id)

    video.check_subtitles()
    video.upload_to_es()
    return video.json_data
