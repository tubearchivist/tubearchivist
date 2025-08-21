"""membership platform views"""

from json import JSONDecodeError

from appsettings.serializers import TokenResponseSerializer
from appsettings.serializers_mb import MembershipProfileSerializer
from appsettings.src.membership import Membership
from common.serializers import ErrorResponseSerializer
from common.src.ta_redis import RedisArchivist
from common.views_base import AdminOnly, ApiBaseView
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.response import Response


class MembershipProfileView(ApiBaseView):
    """resolves to /api/appsettings/membership/profile/
    GET: get profile status
    """

    permission_classes = [AdminOnly]

    @staticmethod
    @extend_schema(
        responses={
            200: OpenApiResponse(MembershipProfileSerializer()),
            400: OpenApiResponse(
                ErrorResponseSerializer(), description="bad request"
            ),
        }
    )
    def get(request):
        """get profile"""

        try:
            profile_response = Membership().get_profile()
        except ValueError as error:
            error = ErrorResponseSerializer({"message": str(error)})
            return Response(error.data, status=400)

        try:
            response_json = profile_response.json()
        except JSONDecodeError:
            code = profile_response.status_code
            message = f"Connection to remote server failed: {code}"
            error_message = {"message": message}
            return Response(error_message, status=400)

        if profile_response.status_code == 403:
            message = response_json.get("detail", "undefined error")
            error_message = {"message": message}
            return Response(error_message, status=400)

        serializer = MembershipProfileSerializer(data=response_json)
        serializer.is_valid(raise_exception=True)

        return Response(serializer.data)


class MembershipSubscriptionSync(ApiBaseView):
    """resolves to /api/appsettings/membership/sync/
    POST: trigger sync task
    """

    permission_classes = [AdminOnly]

    @staticmethod
    def post(request):
        """post request"""
        response = Membership().sync_subs()

        if not response.ok:
            try:
                response_json = response.json()
                message = response_json.get("detail", "undefined error")
            except JSONDecodeError:
                code = response.status_code
                message = f"Connection to remote server failed: {code}"

            error_message = {"message": message}
            return Response(error_message, status=400)

        return Response(status=204)


class MembershipToken(ApiBaseView):
    """resolves to /api/appsettings/membership/token/
    GET: get masked token
    POST: add token
    DELETE: delete token
    """

    permission_classes = [AdminOnly]
    REDIS_KEY = "MB:KEY"

    def get(self, request):
        """get token"""
        token = RedisArchivist().get_message_dict(self.REDIS_KEY)
        if token:
            serializer = TokenResponseSerializer(data=token)
            serializer.is_valid(raise_exception=True)
            data = serializer.data
        else:
            data = {"token": None}

        return Response(data)

    def post(self, request):
        """add token"""
        serializer = TokenResponseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        RedisArchivist().set_message(
            self.REDIS_KEY, message=serializer.data, save=True
        )

        return Response(serializer.data)

    def delete(self, request):
        """delete token"""
        RedisArchivist().del_message(self.REDIS_KEY)

        return Response(status=204)
