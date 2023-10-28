"""
functionality:
- handle snapshots in ES
"""

from datetime import datetime
from time import sleep
from zoneinfo import ZoneInfo

from home.src.es.connect import ElasticWrap
from home.src.ta.helper import get_mapping
from home.src.ta.settings import EnvironmentSettings


class ElasticSnapshot:
    """interact with snapshots on ES"""

    REPO = "ta_snapshot"
    REPO_SETTINGS = {
        "compress": "true",
        "chunk_size": "1g",
        "location": EnvironmentSettings.ES_SNAPSHOT_DIR,
    }
    POLICY = "ta_daily"

    def __init__(self):
        self.all_indices = self._get_all_indices()

    def _get_all_indices(self):
        """return all indices names managed by TA"""
        mapping = get_mapping()
        all_indices = [f"ta_{i['index_name']}" for i in mapping]

        return all_indices

    def setup(self):
        """setup the snapshot in ES, create or update if needed"""
        print("snapshot: run setup")
        repo_exists = self._check_repo_exists()
        if not repo_exists:
            self.create_repo()

        policy_exists = self._check_policy_exists()
        if not policy_exists:
            self.create_policy()

        is_outdated = self._needs_startup_snapshot()
        if is_outdated:
            _ = self.take_snapshot_now()

    def _check_repo_exists(self):
        """check if expected repo already exists"""
        path = f"_snapshot/{self.REPO}"
        response, statuscode = ElasticWrap(path).get()
        if statuscode == 200:
            print(f"snapshot: repo {self.REPO} already created")
            matching = response[self.REPO]["settings"] == self.REPO_SETTINGS
            if not matching:
                print(f"snapshot: update repo settings {self.REPO_SETTINGS}")

            return matching

        print(f"snapshot: setup repo {self.REPO} config {self.REPO_SETTINGS}")
        return False

    def create_repo(self):
        """create filesystem repo"""
        path = f"_snapshot/{self.REPO}"
        data = {
            "type": "fs",
            "settings": self.REPO_SETTINGS,
        }
        response, statuscode = ElasticWrap(path).post(data=data)
        if statuscode == 200:
            print(f"snapshot: repo setup correctly: {response}")

    def _check_policy_exists(self):
        """check if snapshot policy is set correctly"""
        policy = self._get_policy()
        expected_policy = self._build_policy_data()
        if not policy:
            print(f"snapshot: create policy {self.POLICY} {expected_policy}")
            return False

        if policy["policy"] != expected_policy:
            print(f"snapshot: update policy settings {expected_policy}")
            return False

        print("snapshot: policy is set.")
        return True

    def _get_policy(self):
        """get policy from es"""
        path = f"_slm/policy/{self.POLICY}"
        response, statuscode = ElasticWrap(path).get()
        if statuscode != 200:
            return False

        return response[self.POLICY]

    def create_policy(self):
        """create snapshot lifetime policy"""
        path = f"_slm/policy/{self.POLICY}"
        data = self._build_policy_data()
        response, statuscode = ElasticWrap(path).put(data)
        if statuscode == 200:
            print(f"snapshot: policy setup correctly: {response}")

    def _build_policy_data(self):
        """build policy dict from config"""
        at_12 = datetime.now().replace(hour=12, minute=0, second=0)
        hour = at_12.astimezone(ZoneInfo("UTC")).hour

        return {
            "schedule": f"0 0 {hour} * * ?",
            "name": f"<{self.POLICY}_>",
            "repository": self.REPO,
            "config": {
                "indices": self.all_indices,
                "ignore_unavailable": True,
                "include_global_state": True,
            },
            "retention": {
                "expire_after": "30d",
                "min_count": 5,
                "max_count": 50,
            },
        }

    def _needs_startup_snapshot(self):
        """check if last snapshot is expired"""
        snap_dicts = self._get_all_snapshots()
        if not snap_dicts:
            print("snapshot: create initial snapshot")
            return True

        last_stamp = snap_dicts[0]["end_stamp"]
        now = int(datetime.now().timestamp())
        outdated = (now - last_stamp) / 60 / 60 > 24
        if outdated:
            print("snapshot: is outdated, create new now")

        print("snapshot: last snapshot is up-to-date")
        return outdated

    def take_snapshot_now(self, wait=False):
        """execute daily snapshot now"""
        path = f"_slm/policy/{self.POLICY}/_execute"
        response, statuscode = ElasticWrap(path).post()
        if statuscode == 200:
            print(f"snapshot: executing now: {response}")

        if wait:
            self._wait_for_snapshot(response["snapshot_name"])

        return response

    def _wait_for_snapshot(self, snapshot_name):
        """return after snapshot_name completes"""
        path = f"_snapshot/{self.REPO}/{snapshot_name}"

        while True:
            # wait for task to be created
            sleep(1)
            _, statuscode = ElasticWrap(path).get()
            if statuscode == 200:
                break

        while True:
            # wait for snapshot success
            response, statuscode = ElasticWrap(path).get()
            snapshot_state = response["snapshots"][0]["state"]
            if snapshot_state == "SUCCESS":
                break

            print(f"snapshot: {snapshot_name} in state {snapshot_state}")
            print("snapshot: wait to complete")
            sleep(5)

        print(f"snapshot: completed - {response}")

    def get_snapshot_stats(self):
        """get snapshot info for frontend"""
        snapshot_info = self._build_policy_details()
        if snapshot_info:
            snapshot_info.update({"snapshots": self._get_all_snapshots()})

        return snapshot_info

    def get_single_snapshot(self, snapshot_id):
        """get single snapshot metadata"""
        path = f"_snapshot/{self.REPO}/{snapshot_id}"
        response, statuscode = ElasticWrap(path).get()
        if statuscode == 404:
            print(f"snapshots: not found: {snapshot_id}")
            return False

        snapshot = response["snapshots"][0]
        return self._parse_single_snapshot(snapshot)

    def _get_all_snapshots(self):
        """get a list of all registered snapshots"""
        path = f"_snapshot/{self.REPO}/*?sort=start_time&order=desc"
        response, statuscode = ElasticWrap(path).get()
        if statuscode == 404:
            print("snapshots: not configured")
            return False

        all_snapshots = response["snapshots"]
        if not all_snapshots:
            print("snapshots: no snapshots found")
            return False

        snap_dicts = []
        for snapshot in all_snapshots:
            snap_dict = self._parse_single_snapshot(snapshot)
            snap_dicts.append(snap_dict)

        return snap_dicts

    def _parse_single_snapshot(self, snapshot):
        """extract relevant metadata from single snapshot"""
        snap_dict = {
            "id": snapshot["snapshot"],
            "state": snapshot["state"],
            "es_version": snapshot["version"],
            "start_date": self._date_converter(snapshot["start_time"]),
            "end_date": self._date_converter(snapshot["end_time"]),
            "end_stamp": snapshot["end_time_in_millis"] // 1000,
            "duration_s": snapshot["duration_in_millis"] // 1000,
        }
        return snap_dict

    def _build_policy_details(self):
        """get additional policy details"""
        policy = self._get_policy()
        if not policy:
            return False

        next_exec = policy["next_execution_millis"] // 1000
        next_exec_date = datetime.fromtimestamp(next_exec)
        next_exec_str = next_exec_date.strftime("%Y-%m-%d %H:%M")
        expire_after = policy["policy"]["retention"]["expire_after"]
        policy_metadata = {
            "next_exec": next_exec,
            "next_exec_str": next_exec_str,
            "expire_after": expire_after,
        }
        return policy_metadata

    @staticmethod
    def _date_converter(date_utc):
        """convert datetime string"""
        expected_format = "%Y-%m-%dT%H:%M:%S.%fZ"
        date = datetime.strptime(date_utc, expected_format)
        local_datetime = date.replace(tzinfo=ZoneInfo("localtime"))
        converted = local_datetime.astimezone(ZoneInfo(EnvironmentSettings.TZ))
        converted_str = converted.strftime("%Y-%m-%d %H:%M")

        return converted_str

    def restore_all(self, snapshot_name):
        """restore snapshot by name"""
        for index in self.all_indices:
            _, _ = ElasticWrap(index).delete()

        path = f"_snapshot/{self.REPO}/{snapshot_name}/_restore"
        data = {"indices": "*"}
        response, statuscode = ElasticWrap(path).post(data=data)
        if statuscode == 200:
            print(f"snapshot: executing now: {response}")
            return response

        print(f"snapshot: failed to restore, {statuscode} {response}")
        return False

    def delete_single_snapshot(self, snapshot_id):
        """delete single snapshot from index"""
        path = f"_snapshot/{self.REPO}/{snapshot_id}"
        response, statuscode = ElasticWrap(path).delete()
        if statuscode == 200:
            print(f"snapshot: deleting {snapshot_id} {response}")
            return response

        print(f"snapshot: failed to delete, {statuscode} {response}")
        return False
