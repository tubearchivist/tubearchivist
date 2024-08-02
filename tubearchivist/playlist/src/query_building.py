"""build query for playlists"""

from playlist.src.constants import PlaylistTypesEnum


class QueryBuilder:
    """contain functionality"""

    def __init__(self, **kwargs):
        self.request_params = kwargs

    def build_data(self) -> dict:
        """build data dict"""
        data = {}
        data["query"] = self.build_query()
        if sort := self.parse_sort():
            data.update(sort)

        return data

    def build_query(self) -> dict:
        """build query key"""
        must_list = []
        channel = self.request_params.get("channel")
        if channel:
            must_list.append({"match": {"playlist_channel_id": channel[0]}})

        subscribed = self.request_params.get("subscribed")
        if subscribed:
            subed_bool = subscribed[0] == "true"
            must_list.append({"match": {"playlist_subscribed": subed_bool}})

        playlist_type = self.request_params.get("type")
        if playlist_type:
            type_list = self.parse_type(playlist_type[0])
            must_list.append(type_list)

        query = {"bool": {"must": must_list}}

        return query

    def parse_type(self, playlist_type: str) -> dict:
        """parse playlist type"""
        if not hasattr(PlaylistTypesEnum, playlist_type.upper()):
            raise ValueError(f"'{playlist_type}' not in PlaylistTypesEnum")

        type_parsed = getattr(PlaylistTypesEnum, playlist_type.upper()).value

        return {"match": {"playlist_type.keyword": type_parsed}}

    def parse_sort(self) -> dict:
        """return sort"""
        return {"sort": [{"playlist_name.keyword": {"order": "asc"}}]}
