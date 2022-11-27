"""
Functionality:
- Handle json zip file based backup
- create backup
- restore backup
"""

import json
import os
import zipfile
from datetime import datetime

from home.src.es.connect import ElasticWrap, IndexPaginate
from home.src.ta.config import AppConfig
from home.src.ta.helper import get_mapping, ignore_filelist


class ElasticBackup:
    """dump index to nd-json files for later bulk import"""

    def __init__(self, reason=False):
        self.config = AppConfig().config
        self.cache_dir = self.config["application"]["cache_dir"]
        self.timestamp = datetime.now().strftime("%Y%m%d")
        self.index_config = get_mapping()
        self.reason = reason

    def backup_all_indexes(self):
        """backup all indexes, add reason to init"""
        print("backup all indexes")
        if not self.reason:
            raise ValueError("missing backup reason in ElasticBackup")

        for index in self.index_config:
            index_name = index["index_name"]
            print(f"backup: export in progress for {index_name}")
            if not self.index_exists(index_name):
                print(f"skip backup for not yet existing index {index_name}")
                continue

            self.backup_index(index_name)

        self.zip_it()
        if self.reason == "auto":
            self.rotate_backup()

    @staticmethod
    def backup_index(index_name):
        """export all documents of a single index"""
        data = {
            "query": {"match_all": {}},
            "sort": [{"_doc": {"order": "desc"}}],
        }
        paginate = IndexPaginate(
            f"ta_{index_name}", data, keep_source=True, callback=BackupCallback
        )
        _ = paginate.get_results()

    def zip_it(self):
        """pack it up into single zip file"""
        file_name = f"ta_backup-{self.timestamp}-{self.reason}.zip"
        folder = os.path.join(self.cache_dir, "backup")

        to_backup = []
        for file in os.listdir(folder):
            if file.endswith(".json"):
                to_backup.append(os.path.join(folder, file))

        backup_file = os.path.join(folder, file_name)

        comp = zipfile.ZIP_DEFLATED
        with zipfile.ZipFile(backup_file, "w", compression=comp) as zip_f:
            for backup_file in to_backup:
                zip_f.write(backup_file, os.path.basename(backup_file))

        # cleanup
        for backup_file in to_backup:
            os.remove(backup_file)

    def post_bulk_restore(self, file_name):
        """send bulk to es"""
        file_path = os.path.join(self.cache_dir, file_name)
        with open(file_path, "r", encoding="utf-8") as f:
            data = f.read()

        if not data.strip():
            return

        _, _ = ElasticWrap("_bulk").post(data=data, ndjson=True)

    def get_all_backup_files(self):
        """build all available backup files for view"""
        backup_dir = os.path.join(self.cache_dir, "backup")
        backup_files = os.listdir(backup_dir)
        all_backup_files = ignore_filelist(backup_files)
        all_available_backups = [
            i
            for i in all_backup_files
            if i.startswith("ta_") and i.endswith(".zip")
        ]
        all_available_backups.sort(reverse=True)

        backup_dicts = []
        for backup_file in all_available_backups:
            file_split = backup_file.split("-")
            if len(file_split) == 2:
                timestamp = file_split[1].strip(".zip")
                reason = False
            elif len(file_split) == 3:
                timestamp = file_split[1]
                reason = file_split[2].strip(".zip")

            to_add = {
                "filename": backup_file,
                "timestamp": timestamp,
                "reason": reason,
            }
            backup_dicts.append(to_add)

        return backup_dicts

    def restore(self, filename):
        """
        restore from backup zip file
        call reset from ElasitIndexWrap first to start blank
        """
        zip_content = self._unpack_zip_backup(filename)
        self._restore_json_files(zip_content)

    def _unpack_zip_backup(self, filename):
        """extract backup zip and return filelist"""
        backup_dir = os.path.join(self.cache_dir, "backup")
        file_path = os.path.join(backup_dir, filename)

        with zipfile.ZipFile(file_path, "r") as z:
            zip_content = z.namelist()
            z.extractall(backup_dir)

        return zip_content

    def _restore_json_files(self, zip_content):
        """go through the unpacked files and restore"""
        backup_dir = os.path.join(self.cache_dir, "backup")

        for json_f in zip_content:

            file_name = os.path.join(backup_dir, json_f)

            if not json_f.startswith("es_") or not json_f.endswith(".json"):
                os.remove(file_name)
                continue

            print("restoring: " + json_f)
            self.post_bulk_restore(file_name)
            os.remove(file_name)

    @staticmethod
    def index_exists(index_name):
        """check if index already exists to skip"""
        _, status_code = ElasticWrap(f"ta_{index_name}").get()
        exists = status_code == 200

        return exists

    def rotate_backup(self):
        """delete old backups if needed"""
        rotate = self.config["scheduler"]["run_backup_rotate"]
        if not rotate:
            return

        all_backup_files = self.get_all_backup_files()
        auto = [i for i in all_backup_files if i["reason"] == "auto"]

        if len(auto) <= rotate:
            print("no backup files to rotate")
            return

        backup_dir = os.path.join(self.cache_dir, "backup")

        all_to_delete = auto[rotate:]
        for to_delete in all_to_delete:
            file_path = os.path.join(backup_dir, to_delete["filename"])
            print(f"remove old backup file: {file_path}")
            os.remove(file_path)


class BackupCallback:
    """handle backup ndjson writer as callback for IndexPaginate"""

    def __init__(self, source, index_name):
        self.source = source
        self.index_name = index_name
        self.timestamp = datetime.now().strftime("%Y%m%d")

    def run(self):
        """run the junk task"""
        file_content = self._build_bulk()
        self._write_es_json(file_content)

    def _build_bulk(self):
        """build bulk query data from all_results"""
        bulk_list = []

        for document in self.source:
            document_id = document["_id"]
            es_index = document["_index"]
            action = {"index": {"_index": es_index, "_id": document_id}}
            source = document["_source"]
            bulk_list.append(json.dumps(action))
            bulk_list.append(json.dumps(source))

        # add last newline
        bulk_list.append("\n")
        file_content = "\n".join(bulk_list)

        return file_content

    def _write_es_json(self, file_content):
        """write nd-json file for es _bulk API to disk"""
        cache_dir = AppConfig().config["application"]["cache_dir"]
        file_name = f"es_{self.index_name.lstrip('ta_')}-{self.timestamp}.json"
        file_path = os.path.join(cache_dir, "backup", file_name)
        with open(file_path, "a+", encoding="utf-8") as f:
            f.write(file_content)
