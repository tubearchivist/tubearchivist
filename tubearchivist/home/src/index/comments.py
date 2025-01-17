"""
Functionality:
- Download comments
- Index comments in ES
- Retrieve comments from ES
"""

from datetime import datetime

from home.src.download.yt_dlp_base import YtWrap
from home.src.es.connect import ElasticWrap
from home.src.ta.config import AppConfig
from home.src.ta.ta_redis import RedisQueue


class Comments:
    """interact with comments per video"""

    def __init__(self, youtube_id, config=False):
        self.youtube_id = youtube_id
        self.es_path = f"ta_comment/_doc/{youtube_id}"
        self.json_data = False
        self.config = config
        self.is_activated = False
        self.comments_format = False

    def build_json(self):
        """build json document for es"""
        print(f"{self.youtube_id}: get comments")
        self.check_config()
        if not self.is_activated:
            return

        comments_raw, channel_id = self.get_yt_comments()
        if not comments_raw and not channel_id:
            return

        self.format_comments(comments_raw)

        self.json_data = {
            "youtube_id": self.youtube_id,
            "comment_last_refresh": int(datetime.now().timestamp()),
            "comment_channel_id": channel_id,
            "comment_comments": self.comments_format,
        }

    def check_config(self):
        """read config if not attached"""
        if not self.config:
            self.config = AppConfig().config

        self.is_activated = bool(self.config["downloads"]["comment_max"])

    def build_yt_obs(self):
        """
        get extractor config
        max-comments,max-parents,max-replies,max-replies-per-thread
        """
        max_comments = self.config["downloads"]["comment_max"]
        max_comments_list = [i.strip() for i in max_comments.split(",")]
        comment_sort = self.config["downloads"]["comment_sort"]

        yt_obs = {
            "check_formats": None,
            "skip_download": True,
            "getcomments": True,
            "ignoreerrors": True,
            "extractor_args": {
                "youtube": {
                    "max_comments": max_comments_list,
                    "comment_sort": [comment_sort],
                }
            },
        }

        return yt_obs

    def get_yt_comments(self):
        """get comments from youtube"""
        yt_obs = self.build_yt_obs()
        info_json = YtWrap(yt_obs, config=self.config).extract(self.youtube_id)
        if not info_json:
            return False, False

        comments_raw = info_json.get("comments")
        channel_id = info_json.get("channel_id")
        return comments_raw, channel_id

    def format_comments(self, comments_raw):
        """process comments to match format"""
        comments = []

        if comments_raw:
            for comment in comments_raw:
                cleaned_comment = self.clean_comment(comment)
                if not cleaned_comment:
                    continue

                comments.append(cleaned_comment)

        self.comments_format = comments

    def clean_comment(self, comment):
        """parse metadata from comment for indexing"""
        if not comment.get("text"):
            # comment text can be empty
            print(f"{self.youtube_id}: Failed to extract text, {comment}")
            return False

        time_text_datetime = datetime.utcfromtimestamp(comment["timestamp"])

        if time_text_datetime.hour == 0 and time_text_datetime.minute == 0:
            format_string = "%Y-%m-%d"
        else:
            format_string = "%Y-%m-%d %H:%M"

        time_text = time_text_datetime.strftime(format_string)

        if not comment.get("author"):
            comment["author"] = comment.get("author_id", "Unknown")

        cleaned_comment = {
            "comment_id": comment["id"],
            "comment_text": comment["text"].replace("\xa0", ""),
            "comment_timestamp": comment["timestamp"],
            "comment_time_text": time_text,
            "comment_likecount": comment.get("like_count", None),
            "comment_is_favorited": comment.get("is_favorited", False),
            "comment_author": comment["author"],
            "comment_author_id": comment["author_id"],
            "comment_author_thumbnail": comment["author_thumbnail"],
            "comment_author_is_uploader": comment.get(
                "author_is_uploader", False
            ),
            "comment_parent": comment["parent"],
        }

        return cleaned_comment

    def upload_comments(self):
        """upload comments to es"""
        if not self.is_activated:
            return

        print(f"{self.youtube_id}: upload comments")
        _, _ = ElasticWrap(self.es_path).put(self.json_data)

        vid_path = f"ta_video/_update/{self.youtube_id}"
        data = {"doc": {"comment_count": len(self.comments_format)}}
        _, _ = ElasticWrap(vid_path).post(data=data)

    def delete_comments(self):
        """delete comments from es"""
        print(f"{self.youtube_id}: delete comments")
        _, _ = ElasticWrap(self.es_path).delete(refresh=True)

    def get_es_comments(self):
        """get comments from ES"""
        response, statuscode = ElasticWrap(self.es_path).get()
        if statuscode == 404:
            print(f"comments: not found {self.youtube_id}")
            return False

        return response.get("_source")

    def reindex_comments(self):
        """update comments from youtube"""
        self.check_config()
        if not self.is_activated:
            return

        self.build_json()
        if not self.json_data:
            return

        es_comments = self.get_es_comments()

        if not self.comments_format:
            return

        if not self.comments_format and es_comments["comment_comments"]:
            # don't overwrite comments in es
            return

        self.delete_comments()
        self.upload_comments()


class CommentList:
    """interact with comments in group"""

    COMMENT_QUEUE = "index:comment"

    def __init__(self, task=False):
        self.task = task
        self.config = AppConfig().config

    def add(self, video_ids: list[str]) -> None:
        """add list of videos to get comments, if enabled in config"""
        if not self.config["downloads"].get("comment_max"):
            return

        RedisQueue(self.COMMENT_QUEUE).add_list(video_ids)

    def index(self):
        """run comment index"""
        queue = RedisQueue(self.COMMENT_QUEUE)
        while True:
            total = queue.max_score()
            youtube_id, idx = queue.get_next()
            if not youtube_id or not idx or not total:
                break

            if self.task:
                self.notify(idx, total)

            comment = Comments(youtube_id, config=self.config)
            comment.build_json()
            if comment.json_data:
                comment.upload_comments()

    def notify(self, idx, total_videos):
        """send notification on task"""
        message = [f"Add comments for new videos {idx}/{total_videos}"]
        progress = idx / total_videos
        self.task.send_progress(message, progress=progress)
