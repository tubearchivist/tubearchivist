"""all channel API views"""

from appsettings.src.config import AppConfig
from channel.src.index import YoutubeChannel, channel_overwrites
from channel.src.nav import ChannelNav
from common.src.es_connect import ElasticWrap
from common.src.search_processor import SearchProcess
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
    GET: returns the channel specific settings, defaulting to globals
    POST: sets the channel specific settings, returning current values
    """

    permission_classes = [AdminWriteOnly]

    def _get_channel_info(self, channel_id):
        response, status_code = ElasticWrap(
            f"ta_channel/_doc/{channel_id}"
        ).get()
        if status_code != 200:
            raise ValueError()
        try:
            channel_info = SearchProcess(response).process()
        except KeyError:
            raise ValueError()
        return channel_info

    def _current_values(self, channel_id, channel_info=None):
        if channel_info is None:
            channel_info = self._get_channel_info(channel_id)

        _global_config = AppConfig().get_config()
        _defaults = {
            "index_playlists": False,
            "download_format": _global_config["downloads"]["format"],
            "autodelete_days": _global_config["downloads"]["autodelete_days"],
            "integrate_sponsorblock": _global_config["downloads"][
                "integrate_sponsorblock"
            ],
            "subscriptions_channel_size": _global_config["subscriptions"][
                "channel_size"
            ],
            "subscriptions_live_channel_size": _global_config["subscriptions"][
                "live_channel_size"
            ],
            "subscriptions_shorts_channel_size": _global_config[
                "subscriptions"
            ]["shorts_channel_size"],
        }

        return {
            key: channel_info.get("channel_overwrites", {}).get(key, value)
            for key, value in _defaults.items()
        }

    def get(self, request, channel_id):
        # pylint: disable=unused-argument
        try:
            response = self._current_values(channel_id)
        except ValueError:
            return Response({"error": "unknown channel id"}, status=404)
        return Response(response, status=200)

    def post(self, request, channel_id):
        data = request.data
        if not isinstance(data, dict):
            return Response({"error": "invalid payload"}, status=400)

        channel_overwrites(channel_id, data)

        try:
            response = self._current_values(channel_id)
        except ValueError:
            return Response({"error": "unknown channel id"}, status=404)
        return Response(response, status=200)


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
