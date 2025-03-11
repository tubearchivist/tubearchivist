"""all app settings API views"""

from appsettings.serializers import (
    AppConfigSerializer,
    BackupFileSerializer,
    CookieUpdateSerializer,
    CookieValidationSerializer,
    PoTokenSerializer,
    SnapshotCreateResponseSerializer,
    SnapshotItemSerializer,
    SnapshotListSerializer,
    SnapshotRestoreResponseSerializer,
    TokenResponseSerializer,
)
from appsettings.src.backup import ElasticBackup
from appsettings.src.config import AppConfig
from appsettings.src.snapshot import ElasticSnapshot
from common.serializers import (
    AsyncTaskResponseSerializer,
    ErrorResponseSerializer,
)
from common.src.ta_redis import RedisArchivist
from common.views_base import AdminOnly, AdminWriteOnly, ApiBaseView
from django.conf import settings
from download.src.yt_dlp_base import CookieHandler, POTokenHandler
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from task.src.task_manager import TaskCommand
from task.tasks import run_restore_backup


class BackupApiListView(ApiBaseView):
    """resolves to /api/appsettings/backup/
    GET: returns list of available zip backups
    POST: take zip backup now
    """

    permission_classes = [AdminOnly]
    task_name = "run_backup"

    @staticmethod
    @extend_schema(
        responses={
            200: OpenApiResponse(BackupFileSerializer(many=True)),
        },
    )
    def get(request):
        """get list of available backup files"""
        # pylint: disable=unused-argument
        backup_files = ElasticBackup().get_all_backup_files()
        serializer = BackupFileSerializer(backup_files, many=True)
        return Response(serializer.data)

    @extend_schema(
        responses={
            200: OpenApiResponse(AsyncTaskResponseSerializer()),
        },
    )
    def post(self, request):
        """start new backup file task"""
        # pylint: disable=unused-argument
        response = TaskCommand().start(self.task_name)
        message = {
            "message": "backup task started",
            "task_id": response["task_id"],
        }
        serializer = AsyncTaskResponseSerializer(message)

        return Response(serializer.data)


class BackupApiView(ApiBaseView):
    """resolves to /api/appsettings/backup/<filename>/
    GET: return a single backup
    POST: restore backup
    DELETE: delete backup
    """

    permission_classes = [AdminOnly]
    task_name = "restore_backup"

    @staticmethod
    @extend_schema(
        responses={
            200: OpenApiResponse(BackupFileSerializer()),
            404: OpenApiResponse(
                ErrorResponseSerializer(), description="file not found"
            ),
        }
    )
    def get(request, filename):
        """get single backup"""
        # pylint: disable=unused-argument
        backup_file = ElasticBackup().build_backup_file_data(filename)
        if not backup_file:
            error = ErrorResponseSerializer({"error": "file not found"})
            return Response(error.data, status=404)

        serializer = BackupFileSerializer(backup_file)

        return Response(serializer.data)

    @extend_schema(
        responses={
            200: OpenApiResponse(AsyncTaskResponseSerializer()),
            404: OpenApiResponse(
                ErrorResponseSerializer(), description="file not found"
            ),
        }
    )
    def post(self, request, filename):
        """start new task to restore backup file"""
        # pylint: disable=unused-argument
        backup_file = ElasticBackup().build_backup_file_data(filename)
        if not backup_file:
            error = ErrorResponseSerializer({"error": "file not found"})
            return Response(error.data, status=404)

        task = run_restore_backup.delay(filename)
        message = {
            "message": "backup restore task started",
            "filename": filename,
            "task_id": task.id,
        }
        return Response(message)

    @staticmethod
    @extend_schema(
        responses={
            204: OpenApiResponse(description="file deleted"),
            404: OpenApiResponse(
                ErrorResponseSerializer(), description="file not found"
            ),
        }
    )
    def delete(request, filename):
        """delete backup file"""
        # pylint: disable=unused-argument

        backup_file = ElasticBackup().delete_file(filename)
        if not backup_file:
            error = ErrorResponseSerializer({"error": "file not found"})
            return Response(error.data, status=404)

        return Response(status=204)


class AppConfigApiView(ApiBaseView):
    """resolves to /api/appsettings/config/
    GET: return app settings
    POST: update app settings
    """

    permission_classes = [AdminWriteOnly]

    @staticmethod
    @extend_schema(
        responses={
            200: OpenApiResponse(AppConfigSerializer()),
        }
    )
    def get(request):
        """get app config"""
        response = AppConfig().config
        serializer = AppConfigSerializer(response)
        return Response(serializer.data)

    @staticmethod
    @extend_schema(
        request=AppConfigSerializer(),
        responses={
            200: OpenApiResponse(AppConfigSerializer()),
            400: OpenApiResponse(
                ErrorResponseSerializer(), description="Bad request"
            ),
        },
    )
    def post(request):
        """update config values, allows partial update"""
        serializer = AppConfigSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        updated_config = AppConfig().update_config(validated_data)
        updated_serializer = AppConfigSerializer(updated_config)
        return Response(updated_serializer.data)


class CookieView(ApiBaseView):
    """resolves to /api/appsettings/cookie/
    GET: check if cookie is enabled
    POST: verify validity of cookie
    PUT: import cookie
    DELETE: revoke the cookie
    """

    permission_classes = [AdminOnly]

    @extend_schema(
        responses={
            200: OpenApiResponse(CookieValidationSerializer()),
        }
    )
    def get(self, request):
        """get cookie validation status"""
        # pylint: disable=unused-argument
        validation = self._get_cookie_validation()
        serializer = CookieValidationSerializer(validation)

        return Response(serializer.data)

    @extend_schema(
        responses={
            200: OpenApiResponse(CookieValidationSerializer()),
        }
    )
    def post(self, request):
        """validate cookie"""
        # pylint: disable=unused-argument
        config = AppConfig().config
        _ = CookieHandler(config).validate()
        validation = self._get_cookie_validation()
        serializer = CookieValidationSerializer(validation)

        return Response(serializer.data)

    @extend_schema(
        request=CookieUpdateSerializer(),
        responses={
            200: OpenApiResponse(CookieValidationSerializer()),
            400: OpenApiResponse(
                ErrorResponseSerializer(), description="Bad request"
            ),
        },
    )
    def put(self, request):
        """handle put request"""
        # pylint: disable=unused-argument

        serializer = CookieUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        cookie = validated_data.get("cookie")
        if not cookie:
            message = "missing cookie key in request data"
            print(message)
            error = ErrorResponseSerializer({"error": message})
            return Response(error.data, status=400)

        if settings.DEBUG:
            print(f"[cookie] preview:\n\n{cookie[:300]}")

        config = AppConfig().config
        handler = CookieHandler(config)
        handler.set_cookie(cookie)
        validated = handler.validate()
        if not validated:
            message = "[cookie]: import failed, not valid"
            print(message)
            error = ErrorResponseSerializer({"error": message})
            handler.revoke()
            return Response(error.data, status=400)

        validation = self._get_cookie_validation()
        serializer = CookieValidationSerializer(validation)

        return Response(serializer.data)

    @extend_schema(
        responses={
            204: OpenApiResponse(description="Cookie revoked"),
        },
    )
    def delete(self, request):
        """delete the cookie"""
        config = AppConfig().config
        handler = CookieHandler(config)
        handler.revoke()
        return Response(status=204)

    @staticmethod
    def _get_cookie_validation():
        """get current cookie validation"""
        config = AppConfig().config
        validation = RedisArchivist().get_message_dict("cookie:valid")
        is_enabled = {"cookie_enabled": config["downloads"]["cookie_import"]}
        validation.update(is_enabled)

        return validation


class POTokenView(ApiBaseView):
    """handle PO token"""

    permission_classes = [AdminOnly]

    @extend_schema(
        responses={
            200: OpenApiResponse(PoTokenSerializer()),
            404: OpenApiResponse(
                ErrorResponseSerializer(), description="PO token not found"
            ),
        }
    )
    def get(self, request):
        """get PO token"""
        config = AppConfig().config
        potoken = POTokenHandler(config).get()
        if not potoken:
            error = ErrorResponseSerializer({"error": "PO token not found"})
            return Response(error.data, status=404)

        serializer = PoTokenSerializer(data={"potoken": potoken})
        serializer.is_valid(raise_exception=True)

        return Response(serializer.data)

    @extend_schema(
        responses={
            200: OpenApiResponse(PoTokenSerializer()),
            400: OpenApiResponse(
                ErrorResponseSerializer(), description="Bad request"
            ),
        }
    )
    def post(self, request):
        """Update PO token"""
        serializer = PoTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        if not validated_data:
            error = ErrorResponseSerializer(
                {"error": "missing PO token key in request data"}
            )
            return Response(error.data, status=400)

        config = AppConfig().config
        new_token = validated_data["potoken"]

        POTokenHandler(config).set_token(new_token)
        return Response(serializer.data)

    @extend_schema(
        responses={
            204: OpenApiResponse(description="PO token revoked"),
        },
    )
    def delete(self, request):
        """delete PO token"""
        config = AppConfig().config
        POTokenHandler(config).revoke_token()
        return Response(status=204)


class SnapshotApiListView(ApiBaseView):
    """resolves to /api/appsettings/snapshot/
    GET: returns snapshot config plus list of existing snapshots
    POST: take snapshot now
    """

    permission_classes = [AdminOnly]

    @staticmethod
    @extend_schema(
        responses={
            200: OpenApiResponse(SnapshotListSerializer()),
        }
    )
    def get(request):
        """get available snapshots with metadata"""
        # pylint: disable=unused-argument
        snapshots = ElasticSnapshot().get_snapshot_stats()
        serializer = SnapshotListSerializer(snapshots)
        return Response(serializer.data)

    @staticmethod
    @extend_schema(
        responses={
            200: OpenApiResponse(SnapshotCreateResponseSerializer()),
        }
    )
    def post(request):
        """take snapshot now"""
        # pylint: disable=unused-argument
        response = ElasticSnapshot().take_snapshot_now()
        serializer = SnapshotCreateResponseSerializer(response)
        return Response(serializer.data)


class SnapshotApiView(ApiBaseView):
    """resolves to /api/appsettings/snapshot/<snapshot-id>/
    GET: return a single snapshot
    POST: restore snapshot
    DELETE: delete a snapshot
    """

    permission_classes = [AdminOnly]

    @staticmethod
    @extend_schema(
        responses={
            200: OpenApiResponse(SnapshotItemSerializer()),
            404: OpenApiResponse(
                ErrorResponseSerializer(), description="snapshot not found"
            ),
        }
    )
    def get(request, snapshot_id):
        """handle get request"""
        # pylint: disable=unused-argument
        snapshot = ElasticSnapshot().get_single_snapshot(snapshot_id)

        if not snapshot:
            error = ErrorResponseSerializer({"error": "snapshot not found"})
            return Response(error.data, status=404)

        serializer = SnapshotItemSerializer(snapshot)
        return Response(serializer.data)

    @staticmethod
    @extend_schema(
        responses={
            200: OpenApiResponse(SnapshotRestoreResponseSerializer()),
            400: OpenApiResponse(
                ErrorResponseSerializer(), description="bad request"
            ),
        }
    )
    def post(request, snapshot_id):
        """restore snapshot"""
        # pylint: disable=unused-argument
        response = ElasticSnapshot().restore_all(snapshot_id)
        if not response:
            error = ErrorResponseSerializer(
                {"error": "failed to restore snapshot"}
            )
            return Response(error.data, status=400)

        serializer = SnapshotRestoreResponseSerializer(response)

        return Response(serializer.data)

    @staticmethod
    @extend_schema(
        responses={
            204: OpenApiResponse(description="delete snapshot from index"),
        }
    )
    def delete(request, snapshot_id):
        """delete snapshot from index"""
        # pylint: disable=unused-argument
        response = ElasticSnapshot().delete_single_snapshot(snapshot_id)
        if not response:
            error = ErrorResponseSerializer(
                {"error": "failed to delete snapshot"}
            )
            return Response(error.data, status=400)

        return Response(status=204)


class TokenView(ApiBaseView):
    """resolves to /api/appsettings/token/
    GET: get API token
    DELETE: revoke the token
    """

    permission_classes = [AdminOnly]

    @staticmethod
    @extend_schema(
        responses={
            200: OpenApiResponse(TokenResponseSerializer()),
        }
    )
    def get(request):
        """get your API token"""
        token, _ = Token.objects.get_or_create(user=request.user)
        serializer = TokenResponseSerializer({"token": token.key})
        return Response(serializer.data)

    @staticmethod
    @extend_schema(
        responses={
            204: OpenApiResponse(description="delete token"),
        }
    )
    def delete(request):
        """delete your API token, new will get created on next get"""
        print("revoke API token")
        request.user.auth_token.delete()
        return Response(status=204)
