"""all user api views"""

from common.views import ApiBaseView
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.response import Response
from user.models import Account
from user.serializers import AccountSerializer
from user.src.user_config import UserConfig


class UserConfigView(ApiBaseView):
    """resolves to /api/config/user/
    GET: return current user config
    POST: update user config
    """

    def get(self, request):
        """get config"""
        user_id = request.user.id
        account = Account.objects.get(id=user_id)
        serializer = AccountSerializer(account)
        response = serializer.data.copy()

        config = UserConfig(user_id).get_config()
        response.update({"config": config})

        return Response(response)

    def post(self, request):
        """update config"""
        user_id = request.user.id
        data = request.data

        user_conf = UserConfig(user_id)
        for key, value in data.items():
            try:
                user_conf.set_value(key, value)
            except ValueError as err:
                message = {
                    "status": "Bad Request",
                    "message": f"failed updating {key} to '{value}', {err}",
                }
                return Response(message, status=400)

        response = user_conf.get_config()
        response.update({"user_id": user_id})

        return Response(response)


class LoginApiView(ObtainAuthToken):
    """resolves to /api/login/
    POST: return token and username after successful login
    """

    def post(self, request, *args, **kwargs):
        """post data"""
        # pylint: disable=no-member
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, _ = Token.objects.get_or_create(user=user)

        print(f"returning token for user with id {user.pk}")

        return Response(
            {
                "token": token.key,
                "user_id": user.pk,
                "is_superuser": user.is_superuser,
                "is_staff": user.is_staff,
                "user_groups": [group.name for group in user.groups.all()],
            }
        )
