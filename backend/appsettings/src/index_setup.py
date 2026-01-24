"""
functionality:
- setup elastic index at first start
- verify and update index mapping and settings if needed
- backup and restore metadata
"""

from enum import Enum, auto

from appsettings.src.backup import ElasticBackup
from appsettings.src.config import AppConfig
from appsettings.src.snapshot import ElasticSnapshot
from common.src.es_connect import ElasticWrap
from common.src.helper import get_mapping
from deepdiff import DeepDiff
from django.conf import settings


class MappingAction(Enum):
    """index action options"""

    NOOP = auto()
    PUT_MAPPING = auto()
    REINDEX = auto()


class ElasticIndex:
    """interact with a single index"""

    REINDEX_KEYS = {
        "type",
        "analyzer",
        "search_analyzer",
        "normalizer",
        "index",
        "doc_values",
        "norms",
        "ignore_above",
        "enabled",
        "format",
    }

    def __init__(self, index_name, expected_map=False, expected_set=False):
        self.index_name = index_name
        self.expected_map = expected_map
        self.expected_set = expected_set
        self.exists, self.details = self.index_exists()

    @property
    def index_namespace(self) -> str:
        """namespaced index"""
        return f"ta_{self.index_name}"

    def index_exists(self):
        """check if index already exists and return mapping if it does"""
        response, status_code = ElasticWrap(self.index_namespace).get()
        exists = status_code == 200
        if not exists:
            return False, False

        index_key = f"{self.index_namespace}"
        current_version = self.get_current_version()
        if current_version:
            index_key += f"_v{current_version}"

        details = response.get(index_key, False)

        return exists, details

    def get_current_version(self) -> None | int:
        """get current version from aliases of index"""
        response, _ = ElasticWrap(f"{self.index_namespace}/_alias").get()
        if not response:
            raise ValueError("failed to fetch aliases: ", response)

        alias_name = list(response.keys())
        if not alias_name:
            return None

        version_str = alias_name[0].lstrip(f"{self.index_namespace}_v")
        if not version_str:
            # is initial version
            return None

        if not version_str.isdigit():
            raise ValueError("unexpected version_str: ", version_str)

        return int(version_str)

    def validate(self) -> tuple[MappingAction, set[str]]:
        """
        check if all expected mappings and settings match
        returns True when rebuild is needed
        """
        mapping_diff = self._get_mapping_diff()
        removed_fields = self._get_fields_to_delete(diff=mapping_diff)

        if self.expected_set:
            settings_diff = self._validate_settings()
            if settings_diff:
                # treat settings diff as full reindex
                return MappingAction.REINDEX, removed_fields

        if self.expected_map or self.expected_map == {}:
            action = self._classify_mapping_diff(diff=mapping_diff)
            return action, removed_fields

        return MappingAction.NOOP, removed_fields

    def _validate_settings(self):
        """check if all settings are as expected"""

        now_set = self.details["settings"]["index"]

        for key, value in self.expected_set.items():
            if key not in now_set.keys():
                print(key, value)
                return True

            if not value == now_set[key]:
                print(key, value)
                return True

        return False

    def _get_mapping_diff(self) -> DeepDiff:
        """check if all mappings are as expected"""
        now_map = self.details.get("mappings", {}).get("properties", {})
        diff = DeepDiff(
            now_map,
            self.expected_map,
            ignore_order=True,
            report_repetition=True,
            view="tree",
        )
        if diff:
            print(f"[{self.index_namespace}] detected mapping change")
            if settings.DEBUG:
                print(f"[{self.index_namespace}] mapping change: {diff}")

        return diff

    def _classify_mapping_diff(self, diff: DeepDiff) -> MappingAction:
        """use diff to detect what to do"""
        if not diff:
            return MappingAction.NOOP

        if diff.get("type_changes"):
            # always incompatible, needs reindex
            return MappingAction.REINDEX

        added = diff.get("dictionary_item_added", [])
        has_additions = bool(added)

        for item in diff.get("values_changed", []):
            path = item.path(output_format="list")
            if not path:
                continue

            if path[-1] in self.REINDEX_KEYS:
                return MappingAction.REINDEX

            # compatible addition
            has_additions = True

        if has_additions:
            return MappingAction.PUT_MAPPING

        return MappingAction.NOOP

    def _get_fields_to_delete(self, diff: DeepDiff) -> set[str]:
        """fields to remove during next reindex"""
        removed_fields = set()
        for item in diff.get("dictionary_item_removed", []):
            value = item.t1 or {}
            is_field_definition = "type" in value or "properties" in value
            if not is_field_definition:
                continue

            path = item.path(output_format="list")
            removed_fields.add(".".join(path))

        return removed_fields

    def rebuild_index(self, removed_fields: set[str]):
        """rebuild with new mapping"""
        print(f"[{self.index_namespace}] applying new mappings to index")
        current_version = self.get_current_version()

        new_version = current_version + 1 if current_version else 2

        self.create_blank(new_version=new_version)
        self.reindex(new_version=new_version, removed_fields=removed_fields)
        self.delete_index(by_version=current_version)
        self.create_alias(new_version=new_version, old_version=current_version)

    def delete_index(self, by_version: int | None):
        """delete index passed as argument"""
        path = self.index_namespace
        if by_version is not None:
            path += f"_v{by_version}"

        print(f"[{path}] delete index")
        response, status_code = ElasticWrap(path).delete()
        if status_code not in [200, 201]:
            print(f"{status_code}: {response}")
            raise ValueError("index delete failed")

    def create_blank(self, new_version: int | None = None):
        """create blank"""
        path = self.index_namespace
        if new_version is not None:
            path += f"_v{new_version}"

        data = {}
        if self.expected_set:
            data.update({"settings": self.expected_set})
        if self.expected_map or self.expected_map == {}:
            data.update({"mappings": {"properties": self.expected_map}})
            if self.index_name == "config":
                # no indexing for config
                data["mappings"]["dynamic"] = False

        print(f"[{path}] create new blank index")
        if settings.DEBUG:
            print(f"[{path}] creat new blank index with data: {data}")

        response, status_code = ElasticWrap(path).put(data)
        if status_code not in [200, 201]:
            print(f"{status_code}: {response}")
            raise ValueError(f"create blank index {path} failed")

    def reindex(self, new_version: int, removed_fields: set[str]):
        """reindex to versioned new index after creating"""
        source = self.index_namespace
        dest = f"{self.index_namespace}_v{new_version}"
        data: dict = {"source": {"index": source}, "dest": {"index": dest}}

        if removed_fields:
            script = "\n".join(
                f"ctx._source.remove('{i}');" for i in removed_fields
            )
            data["script"] = {"lang": "painless", "source": script}

        msg = f"[{self.index_namespace}] reindex from {source} to {dest}"
        if removed_fields:
            msg += f", remove unexpected fields: {removed_fields}"

        print(msg)

        if settings.DEBUG:
            print(f"send data: {data}")

        path = "_reindex?refresh=true"
        response, status_code = ElasticWrap(path).post(data=data)
        if status_code not in [200, 201]:
            print(f"{status_code}: {response}")
            raise ValueError("reindex failed failed")

    def create_alias(self, new_version: int, old_version: int | None = None):
        """create aliast for moved index"""
        index_new = f"{self.index_namespace}_v{new_version}"
        index_old = None

        data: dict = {
            "actions": [
                {
                    "add": {
                        "index": index_new,
                        "alias": self.index_namespace,
                        "is_write_index": True,
                    },
                },
            ]
        }
        if old_version:
            index_old = f"{self.index_namespace}_v{old_version}"
            data["actions"].append(
                {
                    "remove": {
                        "index": index_old,
                        "alias": self.index_namespace,
                    }
                }
            )

        message = f"create new alias {index_new}"
        if index_old:
            message += f", remove old alias {index_old}"

        print(f"[{self.index_namespace}] {message}")
        if settings.DEBUG:
            print(f"create alias with data: {data}")

        response, status_code = ElasticWrap("_alias").put(data=data)
        if status_code not in [200, 201]:
            print(f"{status_code}: {response}")
            raise ValueError("alias update failed")

    def mapping_update(self):
        """simple mapping update only, use migrations for defaults"""
        current_version = self.get_current_version()
        path = self.index_namespace
        if current_version is not None:
            path += f"_v{current_version}"

        data = {"properties": self.expected_map}
        print(f"[{path}] update mapping")
        if settings.DEBUG:
            print(f"[{path}] update mapping with data: {data}")

        response, status_code = ElasticWrap(f"{path}/_mapping").put(data)
        if status_code not in [200, 201]:
            print(f"{status_code}: {response}")
            raise ValueError(f"create blank index {path} failed")


class ElasticIndexWrap:
    """interact with all index mapping and setup"""

    def __init__(self):
        self.index_config = get_mapping()
        self.backup_run = False

    def setup(self):
        """setup elastic index, run at startup"""
        for index in self.index_config:
            index_name, expected_map, expected_set = self._config_split(index)
            handler = ElasticIndex(index_name, expected_map, expected_set)
            if not handler.exists:
                handler.create_blank()
                continue

            action, removed_fields = handler.validate()
            if action == MappingAction.REINDEX:
                self._check_backup()
                handler.rebuild_index(removed_fields)
                continue

            if action == MappingAction.PUT_MAPPING:
                handler.mapping_update()

            if removed_fields:
                print(
                    f"[ta_{index_name}] skip removing unexpected fields:"
                    + f" {removed_fields}"
                )
            else:
                print(f"[ta_{index_name}] index status is as expected.")

    def reset(self):
        """reset all indexes to blank"""
        self.delete_all()
        self.create_all_blank()

    def delete_all(self):
        """delete all indexes"""
        for index in self.index_config:
            index_name, _, _ = self._config_split(index)
            print(f"[ta_{index_name}] reset elastic index")
            handler = ElasticIndex(index_name)
            if not handler.exists:
                continue

            current_version = handler.get_current_version()
            handler.delete_index(by_version=current_version)

    def create_all_blank(self):
        """create all blank indexes"""
        print("create all new indexes in elastic from template")
        for index in self.index_config:
            index_name, expected_map, expected_set = self._config_split(index)
            handler = ElasticIndex(index_name, expected_map, expected_set)
            handler.create_blank()

    @staticmethod
    def _config_split(index):
        """split index config keys"""
        index_name = index["index_name"]
        expected_map = index["expected_map"]
        expected_set = index["expected_set"]

        return index_name, expected_map, expected_set

    def _check_backup(self):
        """create backup if needed"""
        if self.backup_run:
            return

        try:
            config = AppConfig().config
        except ValueError:
            # create defaults in ES if config not found
            print("AppConfig not found, creating defaults...")
            handler = AppConfig.__new__(AppConfig)
            handler.sync_defaults()
            config = AppConfig.CONFIG_DEFAULTS

        if config["application"]["enable_snapshot"]:
            # take snapshot if enabled
            ElasticSnapshot().take_snapshot_now(wait=True)
        else:
            # fallback to json backup
            ElasticBackup(reason="update").backup_all_indexes()

        self.backup_run = True
