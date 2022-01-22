"""holds es connection manager"""

import json

import requests
from home.src.config import AppConfig


class ElasticWrap:
    """makes all calls to elastic search
    returns response json and status code tuple
    """

    def __init__(self, path, config=False):
        self.url = False
        self.auth = False
        self.path = path
        self.config = config
        self._get_config()

    def _get_config(self):
        """add config if not passed"""
        if not self.config:
            self.config = AppConfig().config

        es_url = self.config["application"]["es_url"]
        self.auth = self.config["application"]["es_auth"]
        self.url = f"{es_url}/{self.path}"

    def get(self, data=False):
        """get data from es"""
        if data:
            response = requests.get(self.url, json=data, auth=self.auth)
        else:
            response = requests.get(self.url, auth=self.auth)
        if not response.ok:
            print(response.text)

        return response.json(), response.status_code

    def post(self, data=False, ndjson=False):
        """post data to es"""
        if ndjson:
            headers = {"Content-type": "application/x-ndjson"}
            payload = data
        else:
            headers = {"Content-type": "application/json"}
            payload = json.dumps(data)

        if data:
            response = requests.post(
                self.url, data=payload, headers=headers, auth=self.auth
            )
        else:
            response = requests.post(self.url, headers=headers, auth=self.auth)

        if not response.ok:
            print(response.text)

        return response.json(), response.status_code

    def put(self, data, refresh=False):
        """put data to es"""
        if refresh:
            self.url = f"{self.url}/?refresh=true"
        response = requests.put(f"{self.url}", json=data, auth=self.auth)
        if not response.ok:
            print(response.text)
            print(data)
            raise ValueError("failed to add item to index")

        return response.json(), response.status_code

    def delete(self, data=False):
        """delete document from es"""
        if data:
            response = requests.delete(self.url, json=data, auth=self.auth)
        else:
            response = requests.delete(self.url, auth=self.auth)

        if not response.ok:
            print(response.text)

        return response.json(), response.status_code


class IndexPaginate:
    """use search_after to go through whole index"""

    DEFAULT_SIZE = 500

    def __init__(self, index_name, data, size=False):
        self.index_name = index_name
        self.data = data
        self.pit_id = False
        self.size = size

    def get_results(self):
        """get all results"""
        self.get_pit()
        self.validate_data()
        all_results = self.run_loop()
        self.clean_pit()
        return all_results

    def get_pit(self):
        """get pit for index"""
        path = f"{self.index_name}/_pit?keep_alive=10m"
        response, _ = ElasticWrap(path).post()
        self.pit_id = response["id"]

    def validate_data(self):
        """add pit and size to data"""
        if "sort" not in self.data.keys():
            print(self.data)
            raise ValueError("missing sort key in data")

        size = self.size or self.DEFAULT_SIZE

        self.data["size"] = size
        self.data["pit"] = {"id": self.pit_id, "keep_alive": "10m"}

    def run_loop(self):
        """loop through results until last hit"""
        all_results = []
        while True:
            response, _ = ElasticWrap("_search").get(data=self.data)
            all_hits = response["hits"]["hits"]
            if all_hits:
                for hit in all_hits:
                    source = hit["_source"]
                    search_after = hit["sort"]
                    all_results.append(source)
                # update search_after with last hit data
                self.data["search_after"] = search_after
            else:
                break

        return all_results

    def clean_pit(self):
        """delete pit from elastic search"""
        data = {"id": self.pit_id}
        ElasticWrap("_pit").delete(data=data)
