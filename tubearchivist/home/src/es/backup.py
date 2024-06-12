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

from home.models import CustomPeriodicTask
from home.src.es.connect import ElasticWrap, IndexPaginate
from home.src.ta.config import AppConfig
from home.src.ta.helper import get_mapping, ignore_filelist
from home.src.ta.settings import EnvironmentSettings


class ElasticBackup:
    """dump index to nd-json files for later bulk import"""

    INDEX_SPLIT = ["comment"]
    CACHE_DIR = EnvironmentSettings.CACHE_DIR
    BACKUP_DIR = os.path.join(CACHE_DIR, "backup")

    def __init__(self, reason=False, task=False):
        self.config = AppConfig().config
        self.timestamp = datetime.now().strftime("%Y%m%d")
        self.index_config = get_mapping()
        self.reason = reason
        self.task = task

    def backup_all_indexes(self):
        """backup all indexes, add reason to init"""
        print("backup all indexes")
        if not self.reason:
            raise ValueError("missing backup reason in ElasticBackup")

        if self.task:
            self.task.send_progress(["Scanning your index."])
        for index in self.index_config:
            index_name = index["index_name"]
            print(f"backup: export in progress for {index_name}")
            if not self.index_exists(index_name):
                print(f"skip backup for not yet existing index {index_name}")
                continue

            self.backup_index(index_name)

        if self.task:
            self.task.send_progress(["Compress files to zip archive."])
        self.zip_it()
        if self.reason == "auto":
            self.rotate_backup()

    def backup_index(self, index_name):
        """export all documents of a single index"""
        paginate_kwargs = {
            "data": {"query": {"match_all": {}}},
            "keep_source": True,
            "callback": BackupCallback,
            "task": self.task,
            "total": self._get_total(index_name),
        }

        if index_name in self.INDEX_SPLIT:
            paginate_kwargs.update({"size": 200})

        paginate = IndexPaginate(f"ta_{index_name}", **paginate_kwargs)
        _ = paginate.get_results()

    @staticmethod
    def _get_total(index_name):
        """get total documents in index"""
        path = f"ta_{index_name}/_count"
        response, _ = ElasticWrap(path).get()

        return response.get("count")

    def zip_it(self):
        """pack it up into single zip file"""
        file_name = f"ta_backup-{self.timestamp}-{self.reason}.zip"

        to_backup = []
        for file in os.listdir(self.BACKUP_DIR):
            if file.endswith(".json"):
                to_backup.append(os.path.join(self.BACKUP_DIR, file))

        backup_file = os.path.join(self.BACKUP_DIR, file_name)

        comp = zipfile.ZIP_DEFLATED
        with zipfile.ZipFile(backup_file, "w", compression=comp) as zip_f:
            for backup_file in to_backup:
                zip_f.write(backup_file, os.path.basename(backup_file))

        # cleanup
        for backup_file in to_backup:
            os.remove(backup_file)

    def post_bulk_restore(self, file_name):
        """send bulk to es"""
        file_path = os.path.join(self.CACHE_DIR, file_name)
        with open(file_path, "r", encoding="utf-8") as f:
            data = f.read()

        if not data.strip():
            return

        _, _ = ElasticWrap("_bulk").post(data=data, ndjson=True)

    def get_all_backup_files(self):
        """build all available backup files for view"""
        all_backup_files = ignore_filelist(os.listdir(self.BACKUP_DIR))
        all_available_backups = [
            i
            for i in all_backup_files
            if i.startswith("ta_") and i.endswith(".zip")
        ]
        all_available_backups.sort(reverse=True)

        backup_dicts = []
        for filename in all_available_backups:
            data = self.build_backup_file_data(filename)
            backup_dicts.append(data)

        return backup_dicts

    def build_backup_file_data(self, filename):
        """build metadata of single backup file"""
        file_path = os.path.join(self.BACKUP_DIR, filename)
        if not os.path.exists(file_path):
            return False

        file_split = filename.split("-")
        if len(file_split) == 2:
            timestamp = file_split[1].strip(".zip")
            reason = False
        elif len(file_split) == 3:
            timestamp = file_split[1]
            reason = file_split[2].strip(".zip")

        data = {
            "filename": filename,
            "file_path": file_path,
            "file_size": os.path.getsize(file_path),
            "timestamp": timestamp,
            "reason": reason,
        }

        return data

    def restore(self, filename):
        """
        restore from backup zip file
        call reset from ElasitIndexWrap first to start blank
        """
        zip_content = self._unpack_zip_backup(filename)
        self._restore_json_files(zip_content)

    def _unpack_zip_backup(self, filename):
        """extract backup zip and return filelist"""
        file_path = os.path.join(self.BACKUP_DIR, filename)

        with zipfile.ZipFile(file_path, "r") as z:
            zip_content = z.namelist()
            z.extractall(self.BACKUP_DIR)

        return zip_content

    def _restore_json_files(self, zip_content):
        """go through the unpacked files and restore"""
        for idx, json_f in enumerate(zip_content):
            self._notify_restore(idx, json_f, len(zip_content))
            file_name = os.path.join(self.BACKUP_DIR, json_f)

            if not json_f.startswith("es_") or not json_f.endswith(".json"):
                os.remove(file_name)
                continue

            print("restoring: " + json_f)
            self.post_bulk_restore(file_name)
            os.remove(file_name)

    def _notify_restore(self, idx, json_f, total_files):
        """notify restore progress"""
        message = [f"Restore index from json backup file {json_f}."]
        progress = (idx + 1) / total_files
        self.task.send_progress(message_lines=message, progress=progress)

    @staticmethod
    def index_exists(index_name):
        """check if index already exists to skip"""
        _, status_code = ElasticWrap(f"ta_{index_name}").get()
        exists = status_code == 200

        return exists

    def rotate_backup(self):
        """delete old backups if needed"""
        try:
            task = CustomPeriodicTask.objects.get(name="run_backup")
        except CustomPeriodicTask.DoesNotExist:
            return

        rotate = task.task_config.get("rotate")
        if not rotate:
            return

        all_backup_files = self.get_all_backup_files()
        auto = [i for i in all_backup_files if i["reason"] == "auto"]

        if len(auto) <= rotate:
            print("no backup files to rotate")
            return

        all_to_delete = auto[rotate:]
        for to_delete in all_to_delete:
            self.delete_file(to_delete["filename"])

    def delete_file(self, filename):
        """delete backup file"""
        file_path = os.path.join(self.BACKUP_DIR, filename)
        if not os.path.exists(file_path):
            print(f"backup file not found: {filename}")
            return False

        print(f"remove old backup file: {file_path}")
        os.remove(file_path)

        return file_path


class BackupCallback:
    """handle backup ndjson writer as callback for IndexPaginate"""

    def __init__(self, source, index_name, counter=0):
        self.source = source
        self.index_name = index_name
        self.counter = counter
        self.timestamp = datetime.now().strftime("%Y%m%d")
        self.cache_dir = EnvironmentSettings.CACHE_DIR

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
        index = self.index_name.lstrip("ta_")
        file_name = f"es_{index}-{self.timestamp}-{self.counter}.json"
        file_path = os.path.join(self.cache_dir, "backup", file_name)
        with open(file_path, "a+", encoding="utf-8") as f:
            f.write(file_content)
