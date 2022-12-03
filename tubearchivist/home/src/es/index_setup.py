"""
functionality:
- setup elastic index at first start
- verify and update index mapping and settings if needed
- backup and restore metadata
"""

from home.src.es.backup import ElasticBackup
from home.src.es.connect import ElasticWrap
from home.src.es.snapshot import ElasticSnapshot
from home.src.ta.config import AppConfig
from home.src.ta.helper import get_mapping


class ElasticIndex:
    """interact with a single index"""

    def __init__(self, index_name, expected_map=False, expected_set=False):
        self.index_name = index_name
        self.expected_map = expected_map
        self.expected_set = expected_set
        self.exists, self.details = self.index_exists()

    def index_exists(self):
        """check if index already exists and return mapping if it does"""
        response, status_code = ElasticWrap(f"ta_{self.index_name}").get()
        exists = status_code == 200
        details = response.get(f"ta_{self.index_name}", False)

        return exists, details

    def validate(self):
        """
        check if all expected mappings and settings match
        returns True when rebuild is needed
        """

        if self.expected_map:
            rebuild = self.validate_mappings()
            if rebuild:
                return rebuild

        if self.expected_set:
            rebuild = self.validate_settings()
            if rebuild:
                return rebuild

        return False

    def validate_mappings(self):
        """check if all mappings are as expected"""
        now_map = self.details["mappings"]["properties"]

        for key, value in self.expected_map.items():
            # nested
            if list(value.keys()) == ["properties"]:
                for key_n, value_n in value["properties"].items():
                    if key not in now_map:
                        print(f"detected mapping change: {key_n}, {value_n}")
                        return True
                    if key_n not in now_map[key]["properties"].keys():
                        print(f"detected mapping change: {key_n}, {value_n}")
                        return True
                    if not value_n == now_map[key]["properties"][key_n]:
                        print(f"detected mapping change: {key_n}, {value_n}")
                        return True

                continue

            # not nested
            if key not in now_map.keys():
                print(f"detected mapping change: {key}, {value}")
                return True
            if not value == now_map[key]:
                print(f"detected mapping change: {key}, {value}")
                return True

        return False

    def validate_settings(self):
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

    def rebuild_index(self):
        """rebuild with new mapping"""
        print(f"applying new mappings to index ta_{self.index_name}...")
        self.create_blank(for_backup=True)
        self.reindex("backup")
        self.delete_index(backup=False)
        self.create_blank()
        self.reindex("restore")
        self.delete_index()

    def reindex(self, method):
        """create on elastic search"""
        if method == "backup":
            source = f"ta_{self.index_name}"
            destination = f"ta_{self.index_name}_backup"
        elif method == "restore":
            source = f"ta_{self.index_name}_backup"
            destination = f"ta_{self.index_name}"

        data = {"source": {"index": source}, "dest": {"index": destination}}
        _, _ = ElasticWrap("_reindex?refresh=true").post(data=data)

    def delete_index(self, backup=True):
        """delete index passed as argument"""
        path = f"ta_{self.index_name}"
        if backup:
            path = path + "_backup"

        _, _ = ElasticWrap(path).delete()

    def create_blank(self, for_backup=False):
        """apply new mapping and settings for blank new index"""
        print(f"create new blank index with name ta_{self.index_name}...")
        path = f"ta_{self.index_name}"
        if for_backup:
            path = f"{path}_backup"

        data = {}
        if self.expected_set:
            data.update({"settings": self.expected_set})
        if self.expected_map:
            data.update({"mappings": {"properties": self.expected_map}})

        _, _ = ElasticWrap(path).put(data)


class ElasitIndexWrap:
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

            rebuild = handler.validate()
            if rebuild:
                self._check_backup()
                handler.rebuild_index()
                continue

            # else all good
            print(f"ta_{index_name} index is created and up to date...")

    def reset(self):
        """reset all indexes to blank"""
        self.delete_all()
        self.create_all_blank()

    def delete_all(self):
        """delete all indexes"""
        print("reset elastic index")
        for index in self.index_config:
            index_name, _, _ = self._config_split(index)
            handler = ElasticIndex(index_name)
            handler.delete_index(backup=False)

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

        config = AppConfig().config
        if config["application"]["enable_snapshot"]:
            # take snapshot if enabled
            ElasticSnapshot().take_snapshot_now(wait=True)
        else:
            # fallback to json backup
            ElasticBackup(reason="update").backup_all_indexes()

        self.backup_run = True
