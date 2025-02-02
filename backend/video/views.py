"""all API views for video endpoints"""

from common.src.helper import calc_is_watched
from common.src.ta_redis import RedisArchivist
from common.src.watched import WatchState
from common.views_base import AdminWriteOnly, ApiBaseView
from playlist.src.index import YoutubePlaylist
from rest_framework.response import Response
from video.src.index import YoutubeVideo
from video.src.query_building import QueryBuilder


class VideoApiListView(ApiBaseView):
    """resolves to /api/video/
    GET: returns list of videos
    params:
    - playlist:str=<playlist-id>
    - channel:str=<channel-id>
    - watch:enum=watched|unwatched|continue
    - sort:enum=published|downloaded|views|likes|duration|filesize
    - order:enum=asc|desc
    - type:enum=videos|streams|shorts
    """

    search_base = "ta_video/_search/"

    def get(self, request):
        """get request"""
        try:
            data = QueryBuilder(request.user.id, **request.GET).build_data()
        except ValueError as err:
            return Response({"error": str(err)}, status=400)

        if data == {"query": {"bool": {"must": [None]}}}:
            # skip empty lookup
            return Response([])

        self.data = data
        self.get_document_list(request, progress_match=request.user.id)

        return Response(self.response)


class VideoApiView(ApiBaseView):
    """resolves to /api/video/<video_id>/
    GET: returns metadata dict of video
    """

    search_base = "ta_video/_doc/"
    permission_classes = [AdminWriteOnly]

    def get(self, request, video_id):
        # pylint: disable=unused-argument
        """get request"""
        self.get_document(video_id, progress_match=request.user.id)
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


class VideoApiNavView(ApiBaseView):
    """resolves to /api/video/<video-id>/nav/
    GET: returns playlist nav
    """

    search_base = "ta_video/_doc/"

    def get(self, request, video_id):
        # pylint: disable=unused-argument
        """get request"""
        self.get_document(video_id)
        if self.status_code != 200:
            return Response(status=self.status_code)

        playlist_nav = []

        if not self.response["data"].get("playlist"):
            return Response(playlist_nav)

        for playlist_id in self.response["data"]["playlist"]:
            playlist = YoutubePlaylist(playlist_id)
            playlist.get_from_es()
            playlist.build_nav(video_id)
            if playlist.nav:
                playlist_nav.append(playlist.nav)

        return Response(playlist_nav, status=self.status_code)


class VideoProgressView(ApiBaseView):
    """resolves to /api/video/<video_id>/progress/
    handle progress status for video
    """

    search_base = "ta_video/_doc/"

    @staticmethod
    def _get_key(user_id: int, video_id: str) -> str:
        """redis key"""
        return f"{user_id}:progress:{video_id}"

    def post(self, request, video_id):
        """set progress position in redis"""
        position = request.data.get("position", 0)
        key = self._get_key(request.user.id, video_id)
        redis_con = RedisArchivist()
        current_progress = redis_con.get_message_dict(key)

        if not current_progress:
            self.get_document(video_id)
            if self.status_code != 200:
                return Response(status=self.status_code)

            current_progress = self.response["data"]["player"]

        current_progress.update({"position": position, "youtube_id": video_id})
        watched = self._check_watched(request, video_id, current_progress)
        if watched:
            expire = 60
        else:
            expire = False

        current_progress.update({"watched": watched})
        redis_con.set_message(key, current_progress, expire=expire)

        return Response(current_progress)

    def _check_watched(self, request, video_id, current_progress) -> bool:
        """check watched state"""
        if current_progress["watched"]:
            return True

        watched = calc_is_watched(
            current_progress["duration"], current_progress["position"]
        )
        if watched:
            WatchState(video_id, watched, request.user.id).change()

        return watched

    def delete(self, request, video_id):
        """delete progress position"""
        key = self._get_key(request.user.id, video_id)
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

        return Response(self.response, status=200)


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
        return Response(self.response, status=200)
