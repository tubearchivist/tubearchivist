"""
functionality:
- wrapper around requests to call elastic search
- reusable search_after to extract total index
"""
# pylint: disable=missing-timeout

import json

import requests
from home.src.ta.config import AppConfig


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

    def get(self, data=False, timeout=10, print_error=True):
        """get data from es"""
        if data:
            response = requests.get(
                self.url, json=data, auth=self.auth, timeout=timeout
            )
        else:
            response = requests.get(self.url, auth=self.auth, timeout=timeout)
        if print_error and not response.ok:
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

    def delete(self, data=False, refresh=False):
        """delete document from es"""
        if refresh:
            self.url = f"{self.url}/?refresh=true"
        if data:
            response = requests.delete(self.url, json=data, auth=self.auth)
        else:
            response = requests.delete(self.url, auth=self.auth)

        if not response.ok:
            print(response.text)

        return response.json(), response.status_code


class IndexPaginate:
    """use search_after to go through whole index
    kwargs:
    - size: int, overwrite DEFAULT_SIZE
    - keep_source: bool, keep _source key from es results
    - callback: obj, Class implementing run method callback for every loop
    - task: task object to send notification
    - total: int, total items in index for progress message
    """

    DEFAULT_SIZE = 500

    def __init__(self, index_name, data, **kwargs):
        self.index_name = index_name
        self.data = data
        self.pit_id = False
        self.kwargs = kwargs

    def get_results(self):
        """get all results, add task and total for notifications"""
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
            self.data.update({"sort": [{"_doc": {"order": "desc"}}]})

        self.data["size"] = self.kwargs.get("size") or self.DEFAULT_SIZE
        self.data["pit"] = {"id": self.pit_id, "keep_alive": "10m"}

    def run_loop(self):
        """loop through results until last hit"""
        all_results = []
        counter = 0
        while True:
            response, _ = ElasticWrap("_search").get(data=self.data)
            all_hits = response["hits"]["hits"]
            if not all_hits:
                break

            for hit in all_hits:
                if self.kwargs.get("keep_source"):
                    all_results.append(hit)
                else:
                    all_results.append(hit["_source"])

            if self.kwargs.get("callback"):
                self.kwargs.get("callback")(all_hits, self.index_name).run()

            if self.kwargs.get("task"):
                print(f"{self.index_name}: processing page {counter}")
                self._notify(len(all_results))

            counter += 1

            # update search_after with last hit data
            self.data["search_after"] = all_hits[-1]["sort"]

        return all_results

    def _notify(self, processed):
        """send notification on task"""
        total = self.kwargs.get("total")
        progress = processed / total
        index_clean = self.index_name.lstrip("ta_").title()
        message = [f"Processing {index_clean}s {processed}/{total}"]
        self.kwargs.get("task").send_progress(message, progress=progress)

    def clean_pit(self):
        """delete pit from elastic search"""
        ElasticWrap("_pit").delete(data={"id": self.pit_id})
