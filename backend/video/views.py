"""all API views for video endpoints"""

from common.src.ta_redis import RedisArchivist
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
