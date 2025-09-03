"""all download API views"""

from common.serializers import (
    AsyncTaskResponseSerializer,
    ErrorResponseSerializer,
)
from common.views_base import AdminOnly, ApiBaseView
from download.serializers import (
    AddToDownloadListSerializer,
    AddToDownloadQuerySerializer,
    BulkUpdateDowloadDataSerializer,
    BulkUpdateDowloadQuerySerializer,
    DownloadAggsSerializer,
    DownloadItemSerializer,
    DownloadListQuerySerializer,
    DownloadListQueueDeleteQuerySerializer,
    DownloadListSerializer,
    DownloadQueueItemUpdateSerializer,
)
from download.src.queue_interact import PendingInteract
from drf_spectacular.utils import OpenApiResponse, extend_schema
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

    @extend_schema(
        responses={
            200: OpenApiResponse(DownloadListSerializer()),
        },
        parameters=[DownloadListQuerySerializer()],
    )
    def get(self, request):
        """get download queue list"""
        query_filter = request.GET.get("filter", False)
        self.data.update(
            {
                "sort": [
                    {"auto_start": {"order": "desc"}},
                    {"timestamp": {"order": "asc"}},
                ],
            }
        )

        serializer = DownloadListQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        must_list = []
        query_filter = validated_data.get("filter")
        if query_filter:
            must_list.append({"term": {"status": {"value": query_filter}}})

        filter_channel = validated_data.get("channel")
        if filter_channel:
            must_list.append(
                {"term": {"channel_id": {"value": filter_channel}}}
            )

        vid_type_filter = validated_data.get("vid_type")
        if vid_type_filter:
            must_list.append(
                {"term": {"vid_type": {"value": vid_type_filter}}}
            )

        search_query = validated_data.get("q")
        if search_query:
            must_list.append({"match_phrase_prefix": {"title": search_query}})

        if validated_data.get("error") is not None:
            operator = "must" if validated_data["error"] else "must_not"
            must_list.append(
                {"bool": {operator: [{"exists": {"field": "message"}}]}}
            )

        self.data["query"] = {"bool": {"must": must_list}}

        self.get_document_list(request)
        serializer = DownloadListSerializer(self.response)

        return Response(serializer.data)

    @staticmethod
    @extend_schema(
        request=AddToDownloadListSerializer(),
        parameters=[AddToDownloadQuerySerializer()],
        responses={
            200: OpenApiResponse(
                AsyncTaskResponseSerializer(),
                description="New async task started",
            ),
            400: OpenApiResponse(
                ErrorResponseSerializer(), description="Bad request"
            ),
        },
    )
    def post(request):
        """add list of videos to download queue"""
        data_serializer = AddToDownloadListSerializer(data=request.data)
        data_serializer.is_valid(raise_exception=True)
        validated_data = data_serializer.validated_data

        query_serializer = AddToDownloadQuerySerializer(
            data=request.query_params
        )
        query_serializer.is_valid(raise_exception=True)
        validated_query = query_serializer.validated_data

        auto_start = validated_query.get("autostart")
        flat = validated_query.get("flat", False)
        force = validated_query.get("force", False)
        print(f"auto_start: {auto_start}, flat: {flat}, force: {force}")
        to_add = validated_data["data"]

        pending = [i["youtube_id"] for i in to_add if i["status"] == "pending"]
        url_str = " ".join(pending)
        print(f"url_str: {url_str}")
        task = extrac_dl.delay(
            url_str, auto_start=auto_start, flat=flat, force=force
        )

        message = {
            "message": "add to queue task started",
            "task_id": task.id,
        }
        response_serializer = AsyncTaskResponseSerializer(message)

        return Response(response_serializer.data)

    @staticmethod
    @extend_schema(
        request=BulkUpdateDowloadDataSerializer(),
        parameters=[BulkUpdateDowloadQuerySerializer()],
        responses={204: OpenApiResponse(description="Status updated")},
    )
    def patch(request):
        """bulk update status"""
        data_serializer = BulkUpdateDowloadDataSerializer(data=request.data)
        data_serializer.is_valid(raise_exception=True)
        validated_data = data_serializer.validated_data

        new_status = validated_data["status"]

        query_serializer = BulkUpdateDowloadQuerySerializer(
            data=request.query_params
        )
        query_serializer.is_valid(raise_exception=True)
        validated_query = query_serializer.validated_data
        status_filter = validated_query.get("filter")

        PendingInteract(status=status_filter).update_bulk(
            channel_id=validated_query.get("channel"),
            vid_type=validated_query.get("vid_type"),
            new_status=validated_data["status"],
            error=validated_query.get("error"),
        )

        if new_status == "priority":
            download_pending.delay(auto_only=True)

        return Response(status=204)

    @extend_schema(
        parameters=[DownloadListQueueDeleteQuerySerializer()],
        responses={
            204: OpenApiResponse(description="Download items deleted"),
            400: OpenApiResponse(
                ErrorResponseSerializer(), description="Bad request"
            ),
        },
    )
    def delete(self, request):
        """bulk delete download queue items by filter"""
        serializer = DownloadListQueueDeleteQuerySerializer(
            data=request.query_params
        )
        serializer.is_valid(raise_exception=True)
        validated_query = serializer.validated_data

        query_filter = validated_query["filter"]
        channel = validated_query.get("channel")
        vid_type = validated_query.get("vid_type")
        message = f"delete queue by status: {query_filter}"
        if channel:
            message += f" - filter by channel: {channel}"
        if vid_type:
            message += f" - filter by vid_type: {vid_type}"

        print(message)
        PendingInteract(status=query_filter).delete_bulk(
            channel_id=channel, vid_type=vid_type
        )

        return Response(status=204)


class DownloadApiView(ApiBaseView):
    """resolves to /api/download/<video_id>/
    GET: returns metadata dict of an item in the download queue
    POST: update status of item to pending or ignore
    DELETE: forget from download queue
    """

    search_base = "ta_download/_doc/"
    valid_status = ["pending", "ignore", "ignore-force", "priority"]
    permission_classes = [AdminOnly]

    @extend_schema(
        responses={
            200: OpenApiResponse(DownloadItemSerializer()),
            404: OpenApiResponse(
                ErrorResponseSerializer(),
                description="Download item not found",
            ),
        },
    )
    def get(self, request, video_id):
        # pylint: disable=unused-argument
        """get download queue item"""
        self.get_document(video_id)
        if not self.response:
            error = ErrorResponseSerializer(
                {"error": "Download item not found"}
            )
            return Response(error.data, status=404)

        response_serializer = DownloadItemSerializer(self.response)

        return Response(response_serializer.data, status=self.status_code)

    @extend_schema(
        request=DownloadQueueItemUpdateSerializer(),
        responses={
            200: OpenApiResponse(
                DownloadQueueItemUpdateSerializer(),
                description="Download item update",
            ),
            400: OpenApiResponse(
                ErrorResponseSerializer(), description="Bad request"
            ),
            404: OpenApiResponse(
                ErrorResponseSerializer(),
                description="Download item not found",
            ),
        },
    )
    def post(self, request, video_id):
        """post to video to change status"""
        data_serializer = DownloadQueueItemUpdateSerializer(data=request.data)
        data_serializer.is_valid(raise_exception=True)
        validated_data = data_serializer.validated_data
        item_status = validated_data["status"]

        if item_status == "ignore-force":
            extrac_dl.delay(video_id, status="ignore")
            return Response(data_serializer.data)

        _, status_code = PendingInteract(video_id).get_item()
        if status_code == 404:
            error = ErrorResponseSerializer(
                {"error": "Download item not found"}
            )
            return Response(error.data, status=404)

        print(f"{video_id}: change status to {item_status}")
        PendingInteract(video_id, item_status).update_status()
        if item_status == "priority":
            download_pending.delay(auto_only=True)

        return Response(data_serializer.data)

    @staticmethod
    @extend_schema(
        responses={
            204: OpenApiResponse(description="delete download item"),
            404: OpenApiResponse(
                ErrorResponseSerializer(),
                description="Download item not found",
            ),
        },
    )
    def delete(request, video_id):
        # pylint: disable=unused-argument
        """delete single video from queue"""
        print(f"{video_id}: delete from queue")
        PendingInteract(video_id).delete_item()

        return Response(status=204)


class DownloadAggsApiView(ApiBaseView):
    """resolves to /api/download/aggs/
    GET: get download aggregations
    """

    search_base = "ta_download/_search"
    valid_filter_view = ["ignore", "pending"]

    @extend_schema(
        parameters=[DownloadListQueueDeleteQuerySerializer()],
        responses={
            200: OpenApiResponse(DownloadAggsSerializer()),
            400: OpenApiResponse(
                ErrorResponseSerializer(), description="bad request"
            ),
        },
    )
    def get(self, request):
        """get aggs"""
        serializer = DownloadListQueueDeleteQuerySerializer(
            data=request.query_params
        )
        serializer.is_valid(raise_exception=True)
        validated_query = serializer.validated_data

        filter_view = validated_query.get("filter")
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
        serializer = DownloadAggsSerializer(self.response["channel_downloads"])

        return Response(serializer.data)
