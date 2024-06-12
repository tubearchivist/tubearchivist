"""
functionality:
- wrapper around requests to call elastic search
- reusable search_after to extract total index
"""

# pylint: disable=missing-timeout

import json
from typing import Any

import requests
import urllib3
from home.src.ta.settings import EnvironmentSettings


class ElasticWrap:
    """makes all calls to elastic search
    returns response json and status code tuple
    """

    def __init__(self, path: str):
        self.url: str = f"{EnvironmentSettings.ES_URL}/{path}"
        self.auth: tuple[str, str] = (
            EnvironmentSettings.ES_USER,
            EnvironmentSettings.ES_PASS,
        )

        if EnvironmentSettings.ES_DISABLE_VERIFY_SSL:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def get(
        self,
        data: bool | dict = False,
        timeout: int = 10,
        print_error: bool = True,
    ) -> tuple[dict, int]:
        """get data from es"""

        kwargs: dict[str, Any] = {
            "auth": self.auth,
            "timeout": timeout,
        }

        if EnvironmentSettings.ES_DISABLE_VERIFY_SSL:
            kwargs["verify"] = False

        if data:
            kwargs["json"] = data

        response = requests.get(self.url, **kwargs)

        if print_error and not response.ok:
            print(response.text)

        return response.json(), response.status_code

    def post(
        self, data: bool | dict = False, ndjson: bool = False
    ) -> tuple[dict, int]:
        """post data to es"""

        kwargs: dict[str, Any] = {"auth": self.auth}

        if ndjson and data:
            kwargs.update(
                {
                    "headers": {"Content-type": "application/x-ndjson"},
                    "data": data,
                }
            )
        elif data:
            kwargs.update(
                {
                    "headers": {"Content-type": "application/json"},
                    "data": json.dumps(data),
                }
            )

        if EnvironmentSettings.ES_DISABLE_VERIFY_SSL:
            kwargs["verify"] = False

        response = requests.post(self.url, **kwargs)

        if not response.ok:
            print(response.text)

        return response.json(), response.status_code

    def put(
        self,
        data: bool | dict = False,
        refresh: bool = False,
    ) -> tuple[dict, Any]:
        """put data to es"""

        if refresh:
            self.url = f"{self.url}/?refresh=true"

        kwargs: dict[str, Any] = {
            "json": data,
            "auth": self.auth,
        }

        if EnvironmentSettings.ES_DISABLE_VERIFY_SSL:
            kwargs["verify"] = False

        response = requests.put(self.url, **kwargs)

        if not response.ok:
            print(response.text)
            print(data)
            raise ValueError("failed to add item to index")

        return response.json(), response.status_code

    def delete(
        self,
        data: bool | dict = False,
        refresh: bool = False,
    ) -> tuple[dict, Any]:
        """delete document from es"""

        if refresh:
            self.url = f"{self.url}/?refresh=true"

        kwargs: dict[str, Any] = {"auth": self.auth}

        if data:
            kwargs["json"] = data

        if EnvironmentSettings.ES_DISABLE_VERIFY_SSL:
            kwargs["verify"] = False

        response = requests.delete(self.url, **kwargs)

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
        if not self.data:
            self.data = {}

        if "query" not in self.data.keys():
            self.data.update({"query": {"match_all": {}}})

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
                self.kwargs.get("callback")(
                    all_hits, self.index_name, counter=counter
                ).run()

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
