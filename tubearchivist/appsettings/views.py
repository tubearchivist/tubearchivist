"""all app settings API views"""

from appsettings.src.backup import ElasticBackup
from appsettings.src.config import AppConfig
from appsettings.src.snapshot import ElasticSnapshot
from common.src.ta_redis import RedisArchivist
from common.views_base import AdminOnly, ApiBaseView
from download.src.yt_dlp_base import CookieHandler
from rest_framework.response import Response
from task.src.task_manager import TaskCommand
from task.tasks import run_restore_backup


class SnapshotApiListView(ApiBaseView):
    """resolves to /api/appsettings/snapshot/
    GET: returns snapshot config plus list of existing snapshots
    POST: take snapshot now
    """

    permission_classes = [AdminOnly]

    @staticmethod
    def get(request):
        """handle get request"""
        # pylint: disable=unused-argument
        snapshots = ElasticSnapshot().get_snapshot_stats()

        return Response(snapshots)

    @staticmethod
    def post(request):
        """take snapshot now with post request"""
        # pylint: disable=unused-argument
        response = ElasticSnapshot().take_snapshot_now()

        return Response(response)


class SnapshotApiView(ApiBaseView):
    """resolves to /api/appsettings/snapshot/<snapshot-id>/
    GET: return a single snapshot
    POST: restore snapshot
    DELETE: delete a snapshot
    """

    permission_classes = [AdminOnly]

    @staticmethod
    def get(request, snapshot_id):
        """handle get request"""
        # pylint: disable=unused-argument
        snapshot = ElasticSnapshot().get_single_snapshot(snapshot_id)

        if not snapshot:
            return Response({"message": "snapshot not found"}, status=404)

        return Response(snapshot)

    @staticmethod
    def post(request, snapshot_id):
        """restore snapshot with post request"""
        # pylint: disable=unused-argument
        response = ElasticSnapshot().restore_all(snapshot_id)
        if not response:
            message = {"message": "failed to restore snapshot"}
            return Response(message, status=400)

        return Response(response)

    @staticmethod
    def delete(request, snapshot_id):
        """delete snapshot from index"""
        # pylint: disable=unused-argument
        response = ElasticSnapshot().delete_single_snapshot(snapshot_id)
        if not response:
            message = {"message": "failed to delete snapshot"}
            return Response(message, status=400)

        return Response(response)


class BackupApiListView(ApiBaseView):
    """resolves to /api/appsettings/backup/
    GET: returns list of available zip backups
    POST: take zip backup now
    """

    permission_classes = [AdminOnly]
    task_name = "run_backup"

    @staticmethod
    def get(request):
        """handle get request"""
        # pylint: disable=unused-argument
        backup_files = ElasticBackup().get_all_backup_files()
        return Response(backup_files)

    def post(self, request):
        """handle post request"""
        # pylint: disable=unused-argument
        response = TaskCommand().start(self.task_name)
        message = {
            "message": "backup task started",
            "task_id": response["task_id"],
        }

        return Response(message)


class BackupApiView(ApiBaseView):
    """resolves to /api/appsettings/backup/<filename>/
    GET: return a single backup
    POST: restore backup
    DELETE: delete backup
    """

    permission_classes = [AdminOnly]
    task_name = "restore_backup"

    @staticmethod
    def get(request, filename):
        """get single backup"""
        # pylint: disable=unused-argument
        backup_file = ElasticBackup().build_backup_file_data(filename)
        if not backup_file:
            message = {"message": "file not found"}
            return Response(message, status=404)

        return Response(backup_file)

    def post(self, request, filename):
        """restore backup file"""
        # pylint: disable=unused-argument
        task = run_restore_backup.delay(filename)
        message = {
            "message": "backup restore task started",
            "filename": filename,
            "task_id": task.id,
        }
        return Response(message)

    @staticmethod
    def delete(request, filename):
        """delete backup file"""
        # pylint: disable=unused-argument

        backup_file = ElasticBackup().delete_file(filename)
        if not backup_file:
            message = {"message": "file not found"}
            return Response(message, status=404)

        message = {"message": f"file {filename} deleted"}
        return Response(message)


class CookieView(ApiBaseView):
    """resolves to /api/appsettings/cookie/
    GET: check if cookie is enabled
    POST: verify validity of cookie
    PUT: import cookie
    """

    permission_classes = [AdminOnly]

    @staticmethod
    def get(request):
        """handle get request"""
        # pylint: disable=unused-argument
        config = AppConfig().config
        valid = RedisArchivist().get_message("cookie:valid")
        response = {"cookie_enabled": config["downloads"]["cookie_import"]}
        response.update(valid)

        return Response(response)

    @staticmethod
    def post(request):
        """handle post request"""
        # pylint: disable=unused-argument
        config = AppConfig().config
        validated = CookieHandler(config).validate()

        return Response({"cookie_validated": validated})

    @staticmethod
    def put(request):
        """handle put request"""
        # pylint: disable=unused-argument
        config = AppConfig().config
        cookie = request.data.get("cookie")
        if not cookie:
            message = "missing cookie key in request data"
            print(message)
            return Response({"message": message}, status=400)

        print(f"cookie preview:\n\n{cookie[:300]}")
        handler = CookieHandler(config)
        handler.set_cookie(cookie)
        validated = handler.validate()
        if not validated:
            handler.revoke()
            message = {"cookie_import": "fail", "cookie_validated": validated}
            print(f"cookie: {message}")
            return Response({"message": message}, status=400)

        message = {"cookie_import": "done", "cookie_validated": validated}
        return Response(message)


class TokenView(ApiBaseView):
    """resolves to /api/appsettings/token/
    DELETE: revoke the token
    """

    permission_classes = [AdminOnly]

    @staticmethod
    def delete(request):
        """delete the token, new will get created automatically"""
        print("revoke API token")
        request.user.auth_token.delete()
        return Response({"success": True})
