"""all channel API views"""

from api.views import AdminWriteOnly, ApiBaseView
from channel.src.index import YoutubeChannel
from download.src.subscriptions import ChannelSubscription
from home.src.ta.urlparser import Parser
from home.tasks import subscribe_to
from rest_framework.response import Response


class ChannelApiView(ApiBaseView):
    """resolves to /api/channel/<channel_id>/
    GET: returns metadata dict of channel
    """

    search_base = "ta_channel/_doc/"
    permission_classes = [AdminWriteOnly]

    def get(self, request, channel_id):
        # pylint: disable=unused-argument
        """get request"""
        self.get_document(channel_id)
        return Response(self.response, status=self.status_code)

    def delete(self, request, channel_id):
        # pylint: disable=unused-argument
        """delete channel"""
        message = {"channel": channel_id}
        try:
            YoutubeChannel(channel_id).delete_channel()
            status_code = 200
            message.update({"state": "delete"})
        except FileNotFoundError:
            status_code = 404
            message.update({"state": "not found"})

        return Response(message, status=status_code)


class ChannelApiListView(ApiBaseView):
    """resolves to /api/channel/
    GET: returns list of channels
    POST: edit a list of channels
    """

    search_base = "ta_channel/_search/"
    valid_filter = ["subscribed"]
    permission_classes = [AdminWriteOnly]

    def get(self, request):
        """get request"""
        self.data.update(
            {"sort": [{"channel_name.keyword": {"order": "asc"}}]}
        )

        query_filter = request.GET.get("filter", False)
        must_list = []
        if query_filter:
            if query_filter not in self.valid_filter:
                message = f"invalid url query filter: {query_filter}"
                print(message)
                return Response({"message": message}, status=400)

            must_list.append({"term": {"channel_subscribed": {"value": True}}})

        self.data["query"] = {"bool": {"must": must_list}}
        self.get_document_list(request)

        return Response(self.response)

    def post(self, request):
        """subscribe/unsubscribe to list of channels"""
        data = request.data
        try:
            to_add = data["data"]
        except KeyError:
            message = "missing expected data key"
            print(message)
            return Response({"message": message}, status=400)

        pending = []
        for channel_item in to_add:
            channel_id = channel_item["channel_id"]
            if channel_item["channel_subscribed"]:
                pending.append(channel_id)
            else:
                self._unsubscribe(channel_id)

        if pending:
            url_str = " ".join(pending)
            subscribe_to.delay(url_str, expected_type="channel")

        return Response(data)

    @staticmethod
    def _unsubscribe(channel_id: str):
        """unsubscribe"""
        print(f"[{channel_id}] unsubscribe from channel")
        ChannelSubscription().change_subscribe(
            channel_id, channel_subscribed=False
        )


class ChannelApiSearchView(ApiBaseView):
    """resolves to /api/channel/search/
    search for channel
    """

    search_base = "ta_channel/_doc/"

    def get(self, request):
        """handle get request, search with s parameter"""

        query = request.GET.get("q")
        if not query:
            message = "missing expected q parameter"
            return Response({"message": message, "data": False}, status=400)

        try:
            parsed = Parser(query).parse()[0]
        except (ValueError, IndexError, AttributeError):
            message = f"channel not found: {query}"
            return Response({"message": message, "data": False}, status=404)

        if not parsed["type"] == "channel":
            message = "expected type channel"
            return Response({"message": message, "data": False}, status=400)

        self.get_document(parsed["url"])

        return Response(self.response, status=self.status_code)


class ChannelApiVideoView(ApiBaseView):
    """resolves to /api/channel/<channel-id>/video
    GET: returns a list of videos of channel
    """

    search_base = "ta_video/_search/"

    def get(self, request, channel_id):
        """handle get request"""
        self.data.update(
            {
                "query": {
                    "term": {"channel.channel_id": {"value": channel_id}}
                },
                "sort": [{"published": {"order": "desc"}}],
            }
        )
        self.get_document_list(request)

        return Response(self.response, status=self.status_code)
