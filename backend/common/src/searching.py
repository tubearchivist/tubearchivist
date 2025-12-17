"""
Functionality:
- handle search to populate results to view
- cache youtube video thumbnails and channel artwork
- parse values in hit_cleanup for frontend
- calculate pagination values
"""

from common.src.es_connect import ElasticWrap
from common.src.search_processor import SearchProcess


class SearchForm:
    """build query from search form data"""

    def multi_search(self, search_query):
        """searching through index"""
        path, query, query_type = SearchParser(search_query).run()
        response, _ = ElasticWrap(path).get(data=query)
        search_results = SearchProcess(response).process()
        all_results = self.build_results(search_results)

        return {"results": all_results, "queryType": query_type}

    @staticmethod
    def build_results(search_results):
        """build the all_results dict"""
        video_results = []
        channel_results = []
        playlist_results = []
        fulltext_results = []
        if search_results:
            for result in search_results:
                if result["_index"] == "ta_video":
                    video_results.append(result)
                elif result["_index"] == "ta_channel":
                    channel_results.append(result)
                elif result["_index"] == "ta_playlist":
                    playlist_results.append(result)
                elif result["_index"] == "ta_subtitle":
                    fulltext_results.append(result)

        all_results = {
            "video_results": video_results,
            "channel_results": channel_results,
            "playlist_results": playlist_results,
            "fulltext_results": fulltext_results,
        }

        return all_results


class SearchParser:
    """handle structured searches"""

    def __init__(self, search_query):
        self.query_words = search_query.lower().split()
        self.query_map = {"term": [], "fuzzy": []}
        self.append_to = "term"

    def run(self):
        """collection, return path and query dict for es"""
        if not self.query_words:
            raise ValueError("empty search query")
        print(f"query words: {self.query_words}")
        query_type = self._find_map()
        self._run_words()
        self._delete_unset()
        self._match_data_types()

        path, query = QueryBuilder(self.query_map, query_type).run()

        return path, query, query_type

    def _find_map(self):
        """find query in keyword map"""
        first_word = self.query_words[0]
        key_word_map = self._get_map()

        if ":" in first_word:
            index_match, query_string = first_word.split(":", 1)
            if index_match in key_word_map:
                self.query_map.update(key_word_map.get(index_match))
                self.query_words[0] = query_string
                if index_match != "video" and self._has_keyword("tag"):
                    raise ValueError("tag: is only supported in video mode")
                return index_match

        if self._has_keyword("tag"):
            self.query_map.update(key_word_map.get("video"))
            return "video"

        self.query_map.update(key_word_map.get("simple"))
        print(f"query_map: {self.query_map}")

        return "simple"

    def _has_keyword(self, keyword):
        """check if query contains keyword: bucket"""
        for word in self.query_words:
            if ":" in word and word.split(":", 1)[0] == keyword:
                return True

        return False

    @staticmethod
    def _get_map():
        """return map to build on"""
        return {
            "simple": {
                "index": "ta_video,ta_channel,ta_playlist",
            },
            "video": {
                "index": "ta_video",
                "channel": [],
                "active": [],
                "tag": [],
            },
            "channel": {
                "index": "ta_channel",
                "active": [],
                "subscribed": [],
            },
            "playlist": {
                "index": "ta_playlist",
                "active": [],
                "subscribed": [],
            },
            "full": {
                "index": "ta_subtitle",
                "lang": [],
                "source": [],
                "channel": [],
            },
        }

    def _run_words(self):
        """append word by word"""
        for word in self.query_words:
            if ":" in word:
                keyword, search_string = word.split(":", 1)
                if keyword in self.query_map:
                    self.append_to = keyword
                    word = search_string

            if word:
                self.query_map[self.append_to].append(word)

    def _delete_unset(self):
        """delete unset keys"""
        new_query_map = {}
        for key, value in self.query_map.items():
            if value:
                new_query_map.update({key: value})
        self.query_map = new_query_map

    def _match_data_types(self):
        """match values with data types"""
        for key, value in self.query_map.items():
            if key in ["term", "channel"]:
                self.query_map[key] = " ".join(self.query_map[key])
            if key in ["active", "subscribed"]:
                self.query_map[key] = "yes" in value


class QueryBuilder:
    """build query for ES from form data"""

    def __init__(self, query_map, query_type):
        self.query_map = query_map
        self.query_type = query_type

    def run(self):
        """build query"""
        path = self._build_path()
        query = self.build_query()
        print(f"es path: {path}")
        print(f"query: {query}")

        return path, query

    def _build_path(self):
        """build es index search path"""
        return f"{self.query_map.get('index')}/_search"

    def build_query(self):
        """build query based on query_type"""

        exec_map = {
            "simple": self._build_simple,
            "video": self._build_video,
            "channel": self._build_channel,
            "playlist": self._build_playlist,
            "full": self._build_fulltext,
        }

        build_must_list = exec_map[self.query_type]

        if self.query_type == "full":
            query = build_must_list()
        else:
            must_list = build_must_list()
            filter_list = []
            if self.query_type == "video":
                if (tags := self.query_map.get("tag")) is not None:
                    filter_list.append(self._build_tag_filter(tags))
            elif self.query_map.get("tag") is not None:
                raise ValueError("tag: is only supported in video mode")

            bool_query = {"must": must_list}
            if filter_list:
                bool_query["filter"] = filter_list

            query = {
                "size": 30,
                "query": {"bool": bool_query},
            }

        return query

    @staticmethod
    def _build_tag_filter(tags):
        """build OR tag filter list for tags.keyword"""
        should_list = []
        for tag in tags:
            should_list.append(QueryBuilder._build_tag_query(tag))

        return {"bool": {"should": should_list, "minimum_should_match": 1}}

    @staticmethod
    def _build_tag_query(tag):
        """build per-tag query clause"""
        if "?" in tag:
            raise ValueError("unsupported wildcard for tag: only trailing * is supported")

        if "*" in tag:
            if tag.count("*") != 1 or not tag.endswith("*") or tag.startswith("*"):
                raise ValueError(
                    "unsupported wildcard for tag: only trailing * is supported"
                )

            prefix_value = tag[:-1]
            if not prefix_value:
                raise ValueError(
                    "unsupported wildcard for tag: only trailing * is supported"
                )

            return {"prefix": {"tags.keyword": {"value": prefix_value}}}

        return {"term": {"tags.keyword": {"value": tag}}}

    def _get_fuzzy(self):
        """return fuziness valuee"""
        fuzzy_value = self.query_map.get("fuzzy", ["auto"])[0]
        if fuzzy_value == "no":
            return 0

        if not fuzzy_value.isdigit():
            return "auto"

        if int(fuzzy_value) > 2:
            return "2"

        return fuzzy_value

    def _build_simple(self):
        """build simple cross index query"""
        must_list = []

        if (term := self.query_map.get("term")) is not None:
            must_list.append(
                {
                    "multi_match": {
                        "query": term,
                        "type": "bool_prefix",
                        "fuzziness": self._get_fuzzy(),
                        "operator": "and",
                        "fields": [
                            "channel_name._2gram",
                            "channel_name._3gram",
                            "channel_name.search_as_you_type",
                            "playlist_name._2gram",
                            "playlist_name._3gram",
                            "playlist_name.search_as_you_type",
                            "title._2gram",
                            "title._3gram",
                            "title.search_as_you_type",
                        ],
                    }
                }
            )

        return must_list

    def _build_video(self):
        """build video query"""
        must_list = []

        if (term := self.query_map.get("term")) is not None:
            must_list.append(
                {
                    "multi_match": {
                        "query": term,
                        "type": "bool_prefix",
                        "fuzziness": self._get_fuzzy(),
                        "operator": "and",
                        "fields": [
                            "title._2gram^2",
                            "title._3gram^2",
                            "title.search_as_you_type^2",
                            "tags",
                            "category",
                        ],
                    }
                }
            )

        if (active := self.query_map.get("active")) is not None:
            must_list.append({"term": {"active": {"value": active}}})

        if (channel := self.query_map.get("channel")) is not None:
            must_list.append(
                {
                    "multi_match": {
                        "query": channel,
                        "type": "bool_prefix",
                        "fuzziness": self._get_fuzzy(),
                        "operator": "and",
                        "fields": [
                            "channel.channel_name._2gram",
                            "channel.channel_name._3gram",
                            "channel.channel_name.search_as_you_type",
                        ],
                    }
                }
            )

        return must_list

    def _build_channel(self):
        """build query for channel"""
        must_list = []

        if (term := self.query_map.get("term")) is not None:
            must_list.append(
                {
                    "multi_match": {
                        "query": term,
                        "type": "bool_prefix",
                        "fuzziness": self._get_fuzzy(),
                        "operator": "and",
                        "fields": [
                            "channel_description",
                            "channel_name._2gram^2",
                            "channel_name._3gram^2",
                            "channel_name.search_as_you_type^2",
                            "channel_tags",
                        ],
                    }
                }
            )

        if (active := self.query_map.get("active")) is not None:
            must_list.append({"term": {"channel_active": {"value": active}}})

        if (subscribed := self.query_map.get("subscribed")) is not None:
            must_list.append(
                {"term": {"channel_subscribed": {"value": subscribed}}}
            )

        return must_list

    def _build_playlist(self):
        """build query for playlist"""
        must_list = []

        if (term := self.query_map.get("term")) is not None:
            must_list.append(
                {
                    "multi_match": {
                        "query": term,
                        "type": "bool_prefix",
                        "fuzziness": self._get_fuzzy(),
                        "operator": "and",
                        "fields": [
                            "playlist_description",
                            "playlist_name._2gram^2",
                            "playlist_name._3gram^2",
                            "playlist_name.search_as_you_type^2",
                        ],
                    }
                }
            )

        if (active := self.query_map.get("active")) is not None:
            must_list.append({"term": {"playlist_active": {"value": active}}})

        if (subscribed := self.query_map.get("subscribed")) is not None:
            must_list.append(
                {"term": {"playlist_subscribed": {"value": subscribed}}}
            )

        return must_list

    def _build_fulltext(self):
        """build query for fulltext search"""
        must_list = []

        if (channel := self.query_map.get("channel")) is not None:
            must_list.append(
                {
                    "multi_match": {
                        "query": channel,
                        "type": "bool_prefix",
                        "fuzziness": self._get_fuzzy(),
                        "operator": "and",
                        "fields": [
                            "subtitle_channel",
                            "subtitle_channel.keyword",
                        ],
                    }
                }
            )

        if (term := self.query_map.get("term")) is not None:
            must_list.append(
                {
                    "match": {
                        "subtitle_line": {
                            "query": term,
                            "fuzziness": self._get_fuzzy(),
                        }
                    }
                }
            )

        if (lang := self.query_map.get("lang")) is not None:
            must_list.append({"term": {"subtitle_lang": {"value": lang[0]}}})

        if (source := self.query_map.get("source")) is not None:
            must_list.append(
                {"term": {"subtitle_source": {"value": source[0]}}}
            )

        query = {
            "size": 30,
            "query": {"bool": {"must": must_list}},
            "highlight": {
                "fields": {
                    "subtitle_line": {
                        "number_of_fragments": 0,
                        "pre_tags": ['<span class="settings-current">'],
                        "post_tags": ["</span>"],
                    }
                }
            },
        }

        return query
