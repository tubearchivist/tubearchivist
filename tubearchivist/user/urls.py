"""all user API urls"""

from django.urls import path
from user import views

urlpatterns = [
    path("login/", views.LoginApiView.as_view(), name="api-user-login"),
    path("me/", views.UserConfigView.as_view(), name="api-user-me"),
]
