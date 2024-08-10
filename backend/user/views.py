"""all user api views"""

from common.views import ApiBaseView
from django.contrib.auth import authenticate, login
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from user.models import Account
from user.serializers import AccountSerializer
from user.src.user_config import UserConfig


class UserConfigView(ApiBaseView):
    """resolves to /api/user/me/
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


@method_decorator(csrf_exempt, name="dispatch")
class LoginApiView(APIView):
    """resolves to /api/user/login/
    POST: return token and username after successful login
    """

    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        """post data"""
        # pylint: disable=no-member

        username = request.data.get("username")
        password = request.data.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)  # Creates a session for the user
            return Response({"message": "Login successful"}, status=200)

        return Response({"message": "Invalid credentials"}, status=400)
