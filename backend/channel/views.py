"""all channel API views"""

from channel.src.index import YoutubeChannel, channel_overwrites
from channel.src.nav import ChannelNav
from common.src.urlparser import Parser
from common.views_base import AdminWriteOnly, ApiBaseView
from download.src.subscriptions import ChannelSubscription
from rest_framework.response import Response
from task.tasks import subscribe_to


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


class ChannelApiAboutView(ApiBaseView):
    """resolves to /api/channel/<channel_id>/about/
    GET: returns the channel specific settings
    POST: sets the channel specific settings, returning current values
    """

    permission_classes = [AdminWriteOnly]

    def get(self, request, channel_id):
        """get channel overwrites"""
        # pylint: disable=unused-argument
        channel = YoutubeChannel(channel_id)
        channel.get_from_es()
        if not channel.json_data:
            return Response({"error": "unknown channel id"}, status=404)

        return Response(channel.get_overwrites())

    def post(self, request, channel_id):
        """modify channel overwrites"""
        data = request.data
        if not isinstance(data, dict):
            return Response({"error": "invalid payload"}, status=400)

        try:
            new_channel_overwrites = channel_overwrites(channel_id, data)
        except ValueError as err:
            return Response({"error": str(err)}, status=400)

        return Response(new_channel_overwrites, status=200)


class ChannelAggsApiView(ApiBaseView):
    """resolves to /api/channel/<channel_id>/aggs/
    GET: get channel aggregations
    """

    search_base = "ta_video/_search"

    def get(self, request, channel_id):
        """get aggs"""
        self.data.update(
            {
                "query": {
                    "term": {"channel.channel_id": {"value": channel_id}}
                },
                "aggs": {
                    "total_items": {"value_count": {"field": "youtube_id"}},
                    "total_size": {"sum": {"field": "media_size"}},
                    "total_duration": {"sum": {"field": "player.duration"}},
                },
            }
        )
        self.get_aggs()

        return Response(self.response)


class ChannelNavApiView(ApiBaseView):
    """resolves to /api/channel/<channel_id>/nav/
    GET: get channel nav
    """

    def get(self, request, channel_id):
        """get nav"""

        nav = ChannelNav(channel_id).get_nav()
        return Response(nav)


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
