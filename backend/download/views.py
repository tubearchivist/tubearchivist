"""all download API views"""

from common.views_base import AdminOnly, ApiBaseView
from download.src.queue import PendingInteract
from rest_framework.response import Response
from task.tasks import download_pending, extrac_dl


class DownloadApiListView(ApiBaseView):
    """resolves to /api/download/
    GET: returns latest videos in the download queue
    POST: add a list of videos to download queue
    DELETE: remove items based on query filter
    """

    search_base = "ta_download/_search/"
    valid_filter = ["pending", "ignore"]
    permission_classes = [AdminOnly]

    def get(self, request):
        """get request"""
        query_filter = request.GET.get("filter", False)
        self.data.update(
            {
                "sort": [
                    {"auto_start": {"order": "desc"}},
                    {"timestamp": {"order": "asc"}},
                ],
            }
        )

        must_list = []
        if query_filter:
            if query_filter not in self.valid_filter:
                message = f"invalid url query filter: {query_filter}"
                print(message)
                return Response({"message": message}, status=400)

            must_list.append({"term": {"status": {"value": query_filter}}})

        filter_channel = request.GET.get("channel", False)
        if filter_channel:
            must_list.append(
                {"term": {"channel_id": {"value": filter_channel}}}
            )

        self.data["query"] = {"bool": {"must": must_list}}

        self.get_document_list(request)
        return Response(self.response)

    @staticmethod
    def post(request):
        """add list of videos to download queue"""
        data = request.data
        auto_start = bool(request.GET.get("autostart"))
        try:
            to_add = data["data"]
        except KeyError:
            message = "missing expected data key"
            print(message)
            return Response({"message": message}, status=400)

        pending = [i["youtube_id"] for i in to_add if i["status"] == "pending"]
        url_str = " ".join(pending)
        extrac_dl.delay(url_str, auto_start=auto_start)

        return Response(data)

    def delete(self, request):
        """delete download queue"""
        query_filter = request.GET.get("filter", False)
        if query_filter not in self.valid_filter:
            message = f"invalid url query filter: {query_filter}"
            print(message)
            return Response({"message": message}, status=400)

        message = f"delete queue by status: {query_filter}"
        print(message)
        PendingInteract(status=query_filter).delete_by_status()

        return Response({"message": message})


class DownloadAggsApiView(ApiBaseView):
    """resolves to /api/download/aggs/
    GET: get download aggregations
    """

    search_base = "ta_download/_search"
    valid_filter_view = ["ignore", "pending"]

    def get(self, request):
        """get aggs"""
        filter_view = request.GET.get("filter")
        if filter_view:
            if filter_view not in self.valid_filter_view:
                message = f"invalid filter: {filter_view}"
                return Response({"message": message}, status=400)

            self.data.update(
                {
                    "query": {"term": {"status": {"value": filter_view}}},
                }
            )

        self.data.update(
            {
                "aggs": {
                    "channel_downloads": {
                        "multi_terms": {
                            "size": 30,
                            "terms": [
                                {"field": "channel_name.keyword"},
                                {"field": "channel_id"},
                            ],
                            "order": {"_count": "desc"},
                        }
                    }
                }
            }
        )
        self.get_aggs()

        return Response(self.response)


class DownloadApiView(ApiBaseView):
    """resolves to /api/download/<video_id>/
    GET: returns metadata dict of an item in the download queue
    POST: update status of item to pending or ignore
    DELETE: forget from download queue
    """

    search_base = "ta_download/_doc/"
    valid_status = ["pending", "ignore", "ignore-force", "priority"]
    permission_classes = [AdminOnly]

    def get(self, request, video_id):
        # pylint: disable=unused-argument
        """get request"""
        self.get_document(video_id)
        return Response(self.response, status=self.status_code)

    def post(self, request, video_id):
        """post to video to change status"""
        item_status = request.data.get("status")
        if item_status not in self.valid_status:
            message = f"{video_id}: invalid status {item_status}"
            print(message)
            return Response({"message": message}, status=400)

        if item_status == "ignore-force":
            extrac_dl.delay(video_id, status="ignore")
            message = f"{video_id}: set status to ignore"
            return Response(request.data)

        _, status_code = PendingInteract(video_id).get_item()
        if status_code == 404:
            message = f"{video_id}: item not found {status_code}"
            return Response({"message": message}, status=404)

        print(f"{video_id}: change status to {item_status}")
        PendingInteract(video_id, item_status).update_status()
        if item_status == "priority":
            download_pending.delay(auto_only=True)

        return Response(request.data)

    @staticmethod
    def delete(request, video_id):
        # pylint: disable=unused-argument
        """delete single video from queue"""
        print(f"{video_id}: delete from queue")
        PendingInteract(video_id).delete_item()

        return Response({"success": True})
