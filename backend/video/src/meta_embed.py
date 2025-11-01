"""bulk metadata embedding"""

from common.src.es_connect import ElasticWrap, IndexPaginate
from video.src.index import YoutubeVideo


class MetadataEmbed:
    """sync metadata to videos in bulk"""

    INDEX_NAME = "ta_video"

    def __init__(self, task=False):
        self.task = task

    def embed(self):
        """entry point"""
        data = {
            "query": {"match_all": {}},
            "_source": ["youtube_id"],
        }
        paginate = IndexPaginate(
            index_name=self.INDEX_NAME,
            data=data,
            size=200,
            callback=MetadataEmbedCallback,
            task=self.task,
            total=self._get_total(),
        )
        _ = paginate.get_results()

    def _get_total(self):
        """get total documents in index"""
        path = f"{self.INDEX_NAME}/_count"
        response, _ = ElasticWrap(path).get()

        return response.get("count")


class MetadataEmbedCallback:
    """callback for metadata embed"""

    def __init__(self, source, index_name, counter=0):
        self.source = source
        self.index_name = index_name
        self.counter = counter

    def run(self):
        """run embed"""
        for video in self.source:
            youtube_id = video["_source"]["youtube_id"]
            YoutubeVideo(youtube_id).embed_metadata()
