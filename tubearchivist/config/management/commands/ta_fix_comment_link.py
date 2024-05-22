"""
comment link fix for update from v0.4.7 to v0.4.8
scan your videos and comments to fix comment_count field
python manage.py ta_fix_comment_link
"""

from django.core.management.base import BaseCommand, CommandError
from home.src.es.connect import ElasticWrap, IndexPaginate


class Command(BaseCommand):
    """fix comment link"""

    def handle(self, *args, **options):
        """run command"""
        self.stdout.write("run comment link fix")
        expected_count = self._get_comment_indexed()
        all_videos = self._get_videos()

        self.stdout.write(f"checking {len(all_videos)} video(s)")
        videos_updated = []
        for video in all_videos:
            video_id = video["youtube_id"]
            comment_count = expected_count.get(video_id)
            if not comment_count:
                continue

            data = {"doc": {"comment_count": comment_count}}
            path = f"ta_video/_update/{video_id}"
            response, status_code = ElasticWrap(path).post(data=data)

            if status_code != 200:
                message = (
                    "failed to add comment count to video"
                    + f"response code: {status_code}"
                    + response
                )
                raise CommandError(message)

            videos_updated.append(video_id)

        self.stdout.write(f"fixed {len(videos_updated)} video(s)")
        self.stdout.write(self.style.SUCCESS("    ✓ task completed\n"))

    def _get_comment_indexed(self):
        """get comment count by index"""
        self.stdout.write("get comments")
        src = "params['_source']['comment_comments'].length"
        data = {
            "script_fields": {
                "comments_length": {
                    "script": {"source": src, "lang": "painless"}
                }
            }
        }
        all_comments = IndexPaginate(
            "ta_comment", data=data, keep_source=True
        ).get_results()

        expected_count = {
            i["_id"]: i["fields"]["comments_length"][0] for i in all_comments
        }

        return expected_count

    def _get_videos(self):
        """get videos without comment_count"""
        self.stdout.write("get videos")
        data = {
            "query": {
                "bool": {"must_not": [{"exists": {"field": "comment_count"}}]}
            }
        }
        all_videos = IndexPaginate("ta_video", data).get_results()

        return all_videos
