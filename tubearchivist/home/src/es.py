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

    def post(self, data, ndjson=False):
        """post data to es"""
        if ndjson:
            headers = {"Content-type": "application/x-ndjson"}
            payload = data
        else:
            headers = {"Content-type": "application/json"}
            payload = json.dumps(data)

        response = requests.post(
            self.url, data=payload, header=headers, auth=self.auth
        )

        if not response.ok:
            print(response.text)

        return response.json(), response.status_code

    def put(self, data):
        """put data to es"""

        response = requests.put(self.url, json=data, auth=self.auth)
        if not response.ok:
            print(response.text)

        return response.json(), response.status_code

    def delete(self):
        """delete document from es"""
        response = requests.delete(self.url, auth=self.auth)
        if not response.ok:
            print(response.text)

        return response.json(), response.status_code
