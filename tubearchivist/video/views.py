"""all API views for video endpoints"""

from api.views import AdminWriteOnly, ApiBaseView
from home.src.ta.ta_redis import RedisArchivist
from rest_framework.response import Response
from video.src.index import YoutubeVideo


class VideoApiView(ApiBaseView):
    """resolves to /api/video/<video_id>/
    GET: returns metadata dict of video
    """

    search_base = "ta_video/_doc/"
    permission_classes = [AdminWriteOnly]

    def get(self, request, video_id):
        # pylint: disable=unused-argument
        """get request"""
        self.get_document(video_id)
        return Response(self.response, status=self.status_code)

    def delete(self, request, video_id):
        # pylint: disable=unused-argument
        """delete single video"""
        message = {"video": video_id}
        try:
            YoutubeVideo(video_id).delete_media_file()
            status_code = 200
            message.update({"state": "delete"})
        except FileNotFoundError:
            status_code = 404
            message.update({"state": "not found"})

        return Response(message, status=status_code)


class VideoApiListView(ApiBaseView):
    """resolves to /api/video/
    GET: returns list of videos
    """

    search_base = "ta_video/_search/"

    def get(self, request):
        """get request"""
        self.data.update({"sort": [{"published": {"order": "desc"}}]})
        self.get_document_list(request)

        return Response(self.response)


class VideoProgressView(ApiBaseView):
    """resolves to /api/video/<video_id>/progress/
    handle progress status for video
    """

    def get(self, request, video_id):
        """get progress for a single video"""
        user_id = request.user.id
        key = f"{user_id}:progress:{video_id}"
        video_progress = RedisArchivist().get_message(key)
        position = video_progress.get("position", 0)

        self.response = {
            "youtube_id": video_id,
            "user_id": user_id,
            "position": position,
        }
        return Response(self.response)

    def post(self, request, video_id):
        """set progress position in redis"""
        position = request.data.get("position", 0)
        key = f"{request.user.id}:progress:{video_id}"
        message = {"position": position, "youtube_id": video_id}
        RedisArchivist().set_message(key, message)
        self.response = request.data
        return Response(self.response)

    def delete(self, request, video_id):
        """delete progress position"""
        key = f"{request.user.id}:progress:{video_id}"
        RedisArchivist().del_message(key)
        self.response = {"progress-reset": video_id}

        return Response(self.response)


class VideoCommentView(ApiBaseView):
    """resolves to /api/video/<video_id>/comment/
    handle video comments
    GET: return all comments from video with reply threads
    """

    search_base = "ta_comment/_doc/"

    def get(self, request, video_id):
        """get video comments"""
        # pylint: disable=unused-argument
        self.get_document(video_id)

        return Response(self.response, status=self.status_code)


class VideoSimilarView(ApiBaseView):
    """resolves to /api/video/<video-id>/similar/
    GET: return max 6 videos similar to this
    """

    search_base = "ta_video/_search/"

    def get(self, request, video_id):
        """get similar videos"""
        self.data = {
            "size": 6,
            "query": {
                "more_like_this": {
                    "fields": ["tags", "title"],
                    "like": {"_id": video_id},
                    "min_term_freq": 1,
                    "max_query_terms": 25,
                }
            },
        }
        self.get_document_list(request, pagination=False)
        return Response(self.response, status=self.status_code)
