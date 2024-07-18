"""
functionality:
- download subtitles
- parse subtitles into it's cues
- index dubtitles
"""

import json
import os
from datetime import datetime

import requests
from home.src.es.connect import ElasticWrap
from home.src.ta.helper import requests_headers
from home.src.ta.settings import EnvironmentSettings


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
        media_url = video_media_url.replace(".mp4", f".{lang}.vtt")
        all_formats = all_subtitles.get(lang)
        if not all_formats:
            return False

        subtitle_json3 = [i for i in all_formats if i["ext"] == "json3"]
        if not subtitle_json3:
            print(f"{self.video.youtube_id}-{lang}: json3 not processed")
            return False

        subtitle = subtitle_json3[0]
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
        media_url = video_media_url.replace(".mp4", f".{lang}.vtt")
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
        videos_base = EnvironmentSettings.MEDIA_DIR
        indexed = []
        for subtitle in relevant_subtitles:
            dest_path = os.path.join(videos_base, subtitle["media_url"])
            source = subtitle["source"]
            lang = subtitle.get("lang")
            response = requests.get(
                subtitle["url"], headers=requests_headers(), timeout=30
            )
            if not response.ok:
                print(f"{self.video.youtube_id}: failed to download subtitle")
                print(response.text)
                continue

            if not response.text:
                print(f"{self.video.youtube_id}: skip empty subtitle")
                continue

            parser = SubtitleParser(response.text, lang, source)
            parser.process()
            if not parser.all_cues:
                continue

            subtitle_str = parser.get_subtitle_str()
            self._write_subtitle_file(dest_path, subtitle_str)
            if self.video.config["downloads"]["subtitle_index"]:
                query_str = parser.create_bulk_import(self.video, source)
                self._index_subtitle(query_str)

            indexed.append(subtitle)

        return indexed

    def _write_subtitle_file(self, dest_path, subtitle_str):
        """write subtitle file to disk"""
        # create folder here for first video of channel
        os.makedirs(os.path.split(dest_path)[0], exist_ok=True)
        with open(dest_path, "w", encoding="utf-8") as subfile:
            subfile.write(subtitle_str)

        host_uid = EnvironmentSettings.HOST_UID
        host_gid = EnvironmentSettings.HOST_GID
        if host_uid and host_gid:
            os.chown(dest_path, host_uid, host_gid)

    @staticmethod
    def _index_subtitle(query_str):
        """send subtitle to es for indexing"""
        _, _ = ElasticWrap("_bulk").post(data=query_str, ndjson=True)

    def delete(self, subtitles=False):
        """delete subtitles from index and filesystem"""
        youtube_id = self.video.youtube_id
        videos_base = EnvironmentSettings.MEDIA_DIR
        # delete files
        if subtitles:
            files = [i["media_url"] for i in subtitles]
        else:
            if not self.video.json_data.get("subtitles"):
                return

            files = [i["media_url"] for i in self.video.json_data["subtitles"]]

        for file_name in files:
            file_path = os.path.join(videos_base, file_name)
            try:
                os.remove(file_path)
            except FileNotFoundError:
                print(f"{youtube_id}: {file_path} failed to delete")
        # delete from index
        path = "ta_subtitle/_delete_by_query?refresh=true"
        data = {"query": {"term": {"youtube_id": {"value": youtube_id}}}}
        _, _ = ElasticWrap(path).post(data=data)


class SubtitleParser:
    """parse subtitle str from youtube"""

    def __init__(self, subtitle_str, lang, source):
        self.subtitle_raw = json.loads(subtitle_str)
        self.lang = lang
        self.source = source
        self.all_cues = False

    def process(self):
        """extract relevant que data"""
        self.all_cues = []
        all_events = self.subtitle_raw.get("events")

        if not all_events:
            return

        if self.source == "auto":
            all_events = self._flat_auto_caption(all_events)

        for idx, event in enumerate(all_events):
            if "dDurationMs" not in event or "segs" not in event:
                # some events won't have a duration or segs
                print(f"skipping subtitle event without content: {event}")
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
                last = flatten[-1]
                if "dDurationMs" not in last or "segs" not in last:
                    # some events won't have a duration or segs
                    print(f"skipping subtitle event without content: {event}")
                    continue

                last_end = last["tStartMs"] + last["dDurationMs"]
                if event["tStartMs"] < last_end:
                    joined = last["segs"][0]["utf8"] + "\n" + text
                    last["segs"][0]["utf8"] = joined
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
            "subtitle_last_refresh": int(datetime.now().timestamp()),
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
