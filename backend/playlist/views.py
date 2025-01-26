"""all playlist API views"""

import uuid

from common.views_base import AdminWriteOnly, ApiBaseView
from download.src.subscriptions import PlaylistSubscription
from playlist.src.index import YoutubePlaylist
from playlist.src.query_building import QueryBuilder
from rest_framework import status
from rest_framework.response import Response
from task.tasks import subscribe_to
from user.src.user_config import UserConfig


class PlaylistApiListView(ApiBaseView):
    """resolves to /api/playlist/
    GET: returns list of indexed playlists
    params:
    - channel:str=<channel-id>
    - subscribed: bool
    - type:enum=regular|custom
    POST: change subscribe state
    """

    search_base = "ta_playlist/_search/"
    permission_classes = [AdminWriteOnly]

    def get(self, request):
        """get request"""
        try:
            data = QueryBuilder(**request.GET).build_data()
        except ValueError as err:
            return Response({"error": str(err)}, status=400)

        self.data = data
        self.get_document_list(request)

        return Response(self.response)

    def post(self, request):
        """subscribe/unsubscribe to list of playlists"""
        data = request.data
        try:
            to_add = data["data"]
        except KeyError:
            message = "missing expected data key"
            print(message)
            return Response({"message": message}, status=400)

        data = data["data"]
        if isinstance(data, dict):
            custom_name = data.get("create")
            if custom_name:
                playlist_id = f"TA_playlist_{uuid.uuid4()}"
                custom_playlist = YoutubePlaylist(playlist_id)
                custom_playlist.create(custom_name)
                return Response(custom_playlist.json_data)

        pending = []
        for playlist_item in to_add:
            playlist_id = playlist_item["playlist_id"]
            if playlist_item["playlist_subscribed"]:
                pending.append(playlist_id)
            else:
                self._unsubscribe(playlist_id)

        if pending:
            url_str = " ".join(pending)
            subscribe_to.delay(url_str, expected_type="playlist")

        return Response(data)

    @staticmethod
    def _unsubscribe(playlist_id: str):
        """unsubscribe"""
        print(f"[{playlist_id}] unsubscribe from playlist")
        _ = PlaylistSubscription().change_subscribe(
            playlist_id, subscribe_status=False
        )


class PlaylistApiView(ApiBaseView):
    """resolves to /api/playlist/<playlist_id>/
    GET: returns metadata dict of playlist
    """

    search_base = "ta_playlist/_doc/"
    permission_classes = [AdminWriteOnly]
    valid_custom_actions = ["create", "remove", "up", "down", "top", "bottom"]

    def get(self, request, playlist_id):
        # pylint: disable=unused-argument
        """get request"""
        self.get_document(playlist_id)
        return Response(self.response, status=self.status_code)

    def post(self, request, playlist_id):
        """post to custom playlist to add a video to list"""
        self.get_document(playlist_id)
        if not self.response["data"]:
            return Response({"error": "playlist not found"}, status=404)

        data = request.data
        subscribed = data.get("playlist_subscribed")
        if subscribed is not None:
            playlist_sub = PlaylistSubscription()
            json_data = playlist_sub.change_subscribe(playlist_id, subscribed)
            return Response(json_data, status=200)

        if not self.response["data"]["playlist_type"] == "custom":
            message = f"playlist with ID {playlist_id} is not custom"
            return Response({"message": message}, status=400)

        action = request.data.get("action")
        if action not in self.valid_custom_actions:
            message = f"invalid action: {action}"
            return Response({"message": message}, status=400)

        playlist = YoutubePlaylist(playlist_id)
        video_id = request.data.get("video_id")
        if action == "create":
            playlist.add_video_to_playlist(video_id)
        else:
            hide = UserConfig(request.user.id).get_value("hide_watched")
            playlist.move_video(video_id, action, hide_watched=hide)

        return Response({"success": True}, status=status.HTTP_201_CREATED)

    def delete(self, request, playlist_id):
        """delete playlist"""
        print(f"{playlist_id}: delete playlist")
        delete_videos = request.GET.get("delete-videos", False)
        if delete_videos:
            YoutubePlaylist(playlist_id).delete_videos_playlist()
        else:
            YoutubePlaylist(playlist_id).delete_metadata()

        return Response({"success": True})
