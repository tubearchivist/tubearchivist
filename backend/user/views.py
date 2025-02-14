"""all user api views"""

from common.serializers import ErrorResponseSerializer
from common.views import ApiBaseView
from django.contrib.auth import authenticate, login, logout
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from user.models import Account
from user.serializers import (
    AccountSerializer,
    LoginSerializer,
    UserMeConfigSerializer,
)
from user.src.user_config import UserConfig


class UserAccountView(ApiBaseView):
    """resolves to /api/user/account/
    GET: return current user account
    """

    @extend_schema(
        responses=AccountSerializer(),
    )
    def get(self, request):
        """get user account"""
        user_id = request.user.id
        account = Account.objects.get(id=user_id)
        account_serializer = AccountSerializer(account)
        return Response(account_serializer.data)


class UserConfigView(ApiBaseView):
    """resolves to /api/user/me/
    GET: return current user config
    POST: update user config
    """

    @extend_schema(responses=UserMeConfigSerializer())
    def get(self, request):
        """get user config"""
        config = UserConfig(request.user.id).get_config()
        serializer = UserMeConfigSerializer(config)

        return Response(serializer.data)

    @extend_schema(
        request=UserMeConfigSerializer(required=False),
        responses={
            200: UserMeConfigSerializer(),
            400: OpenApiResponse(
                ErrorResponseSerializer(), description="Bad request"
            ),
        },
    )
    def post(self, request):
        """update config, allows partial update"""

        data_serializer = UserMeConfigSerializer(
            data=request.data, partial=True
        )
        data_serializer.is_valid(raise_exception=True)
        validated_data = data_serializer.validated_data
        UserConfig(request.user.id).update_config(to_update=validated_data)
        config = UserConfig(request.user.id).get_config()
        serializer = UserMeConfigSerializer(config)

        return Response(serializer.data)


@method_decorator(csrf_exempt, name="dispatch")
class LoginApiView(APIView):
    """resolves to /api/user/login/
    POST: return token and username after successful login
    """

    permission_classes = [AllowAny]
    SEC_IN_DAY = 60 * 60 * 24

    @extend_schema(
        request=LoginSerializer(),
        responses={204: OpenApiResponse(description="login successful")},
    )
    def post(self, request, *args, **kwargs):
        """login with username and password"""
        # pylint: disable=no-member
        data_serializer = LoginSerializer(data=request.data)
        data_serializer.is_valid(raise_exception=True)
        validated_data = data_serializer.validated_data

        username = validated_data["username"]
        password = validated_data["password"]
        remember_me = validated_data.get("remember_me")

        user = authenticate(request, username=username, password=password)
        if user is None:
            error = ErrorResponseSerializer({"error": "Invalid credentials"})
            return Response(error.data, status=400)

        if remember_me == "on":
            request.session.set_expiry(self.SEC_IN_DAY * 365)
        else:
            request.session.set_expiry(self.SEC_IN_DAY * 2)

        print(f"expire session in {request.session.get_expiry_age()} secs")

        login(request, user)  # Creates a session for the user
        return Response(status=204)


class LogoutApiView(ApiBaseView):
    """resolves to /api/user/logout/
    POST: handle logout
    """

    @extend_schema(
        responses={204: OpenApiResponse(description="logout successful")}
    )
    def post(self, request, *args, **kwargs):
        """logout user from session"""
        logout(request)
        return Response(status=204)
