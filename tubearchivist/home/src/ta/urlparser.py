"""
Functionality:
- detect valid youtube ids and links from multi line string
- identify vid_type if possible
"""

from urllib.parse import parse_qs, urlparse

from home.src.download.yt_dlp_base import YtWrap
from home.src.index.video_constants import VideoTypeEnum


class Parser:
    """take a multi line string and detect valid youtube ids"""

    def __init__(self, url_str):
        self.url_list = [i.strip() for i in url_str.split()]

    def parse(self):
        """parse the list"""
        ids = []
        for url in self.url_list:
            parsed = urlparse(url)
            if parsed.netloc:
                # is url
                identified = self.process_url(parsed)
            else:
                # is not url
                identified = self._find_valid_id(url)

            if "vid_type" not in identified:
                identified.update(self._detect_vid_type(parsed.path))

            ids.append(identified)

        return ids

    def process_url(self, parsed):
        """process as url"""
        if parsed.netloc == "youtu.be":
            # shortened
            youtube_id = parsed.path.strip("/")
            return self._validate_expected(youtube_id, "video")

        if "youtube.com" not in parsed.netloc:
            message = f"invalid domain: {parsed.netloc}"
            raise ValueError(message)

        query_parsed = parse_qs(parsed.query)
        if "v" in query_parsed:
            # video from v query str
            youtube_id = query_parsed["v"][0]
            return self._validate_expected(youtube_id, "video")

        if "list" in query_parsed:
            # playlist from list query str
            youtube_id = query_parsed["list"][0]
            return self._validate_expected(youtube_id, "playlist")

        all_paths = parsed.path.strip("/").split("/")
        if all_paths[0] == "shorts":
            # is shorts video
            item = self._validate_expected(all_paths[1], "video")
            item.update({"vid_type": VideoTypeEnum.SHORTS.value})
            return item

        if all_paths[0] == "channel":
            return self._validate_expected(all_paths[1], "channel")

        # detect channel
        channel_id = self._extract_channel_name(parsed.geturl())
        return {"type": "channel", "url": channel_id}

    def _validate_expected(self, youtube_id, expected_type):
        """raise value error if not matching"""
        matched = self._find_valid_id(youtube_id)
        if matched["type"] != expected_type:
            raise ValueError(
                f"{youtube_id} not of expected type {expected_type}"
            )

        return {"type": expected_type, "url": youtube_id}

    def _find_valid_id(self, id_str):
        """detect valid id from length of string"""
        if id_str in ("LL", "WL"):
            return {"type": "playlist", "url": id_str}

        if id_str.startswith("@"):
            url = f"https://www.youtube.com/{id_str}"
            channel_id = self._extract_channel_name(url)
            return {"type": "channel", "url": channel_id}

        len_id_str = len(id_str)
        if len_id_str == 11:
            item_type = "video"
        elif len_id_str == 24:
            item_type = "channel"
        elif len_id_str in (34, 26, 18) or id_str.startswith("TA_playlist_"):
            item_type = "playlist"
        else:
            raise ValueError(f"not a valid id_str: {id_str}")

        return {"type": item_type, "url": id_str}

    @staticmethod
    def _extract_channel_name(url):
        """find channel id from channel name with yt-dlp help"""
        obs_request = {
            "check_formats": None,
            "skip_download": True,
            "extract_flat": True,
            "playlistend": 0,
        }
        url_info = YtWrap(obs_request).extract(url)
        channel_id = url_info.get("channel_id", False)
        if channel_id:
            return channel_id

        url = url_info.get("url", False)
        if url:
            # handle old channel name redirect with url path split
            channel_id = urlparse(url).path.strip("/").split("/")[1]

            return channel_id

        print(f"failed to extract channel id from {url}")
        raise ValueError

    def _detect_vid_type(self, path):
        """try to match enum from path, needs to be serializable"""
        last = path.strip("/").split("/")[-1]
        try:
            vid_type = VideoTypeEnum(last).value
        except ValueError:
            vid_type = VideoTypeEnum.UNKNOWN.value

        return {"vid_type": vid_type}
