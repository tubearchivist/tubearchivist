"""interact with queue items"""

from common.src.es_connect import ElasticWrap


class PendingInteract:
    """interact with items in download queue"""

    def __init__(self, youtube_id=False, status=False):
        self.youtube_id = youtube_id
        self.status = status

    def delete_item(self):
        """delete single item from pending"""
        path = f"ta_download/_doc/{self.youtube_id}"
        _, _ = ElasticWrap(path).delete(refresh=True)

    def delete_bulk(self, channel_id: str | None, vid_type: str | None):
        """delete all matching item by status"""
        must_list = [{"term": {"status": {"value": self.status}}}]
        if channel_id:
            must_list.append({"term": {"channel_id": {"value": channel_id}}})

        if vid_type:
            must_list.append({"term": {"vid_type": {"value": vid_type}}})

        data = {"query": {"bool": {"must": must_list}}}

        path = "ta_download/_delete_by_query?refresh=true"
        _, _ = ElasticWrap(path).post(data=data)

    def update_bulk(
        self,
        channel_id: str | None,
        vid_type: str | None,
        new_status: str,
        error: bool | None = None,
    ):
        """update status in bulk"""
        must_list = [{"term": {"status": {"value": self.status}}}]
        must_not_list = []

        if channel_id:
            must_list.append({"term": {"channel_id": {"value": channel_id}}})

        if vid_type:
            must_list.append({"term": {"vid_type": {"value": vid_type}}})

        if error is not None:
            exists = {"exists": {"field": "message"}}
            if error:
                must_list.append(exists)  # type: ignore
            else:
                must_not_list.append(exists)

        if new_status == "priority":
            source = """
            ctx._source.status = 'pending';
            ctx._source.auto_start = true;
            ctx._source.message = null;
            """
        elif new_status == "clear_error":
            source = "ctx._source.message = null"
        else:
            source = f"ctx._source.status = '{new_status}'"

        data = {
            "query": {"bool": {"must": must_list, "must_not": must_not_list}},
            "script": {"source": source, "lang": "painless"},
        }

        path = "ta_download/_update_by_query?refresh=true"
        _, _ = ElasticWrap(path).post(data)

    def update_status(self):
        """update status of pending item"""
        if self.status == "priority":
            data = {
                "doc": {
                    "status": "pending",
                    "auto_start": True,
                    "message": None,
                }
            }
        else:
            data = {"doc": {"status": self.status}}

        path = f"ta_download/_update/{self.youtube_id}/?refresh=true"
        _, _ = ElasticWrap(path).post(data=data)

    def get_item(self):
        """return pending item dict"""
        path = f"ta_download/_doc/{self.youtube_id}"
        response, status_code = ElasticWrap(path).get()
        return response["_source"], status_code

    def get_channel(self):
        """
        get channel metadata from queue to not depend on channel to be indexed
        """
        data = {
            "size": 1,
            "query": {"term": {"channel_id": {"value": self.youtube_id}}},
        }
        response, _ = ElasticWrap("ta_download/_search").get(data=data)
        hits = response["hits"]["hits"]
        if not hits:
            channel_name = "NA"
        else:
            channel_name = hits[0]["_source"].get("channel_name", "NA")

        return {
            "channel_id": self.youtube_id,
            "channel_name": channel_name,
        }
