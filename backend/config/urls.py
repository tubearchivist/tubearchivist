"""config URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("api/", include("common.urls")),
    path("api/video/", include("video.urls")),
    path("api/channel/", include("channel.urls")),
    path("api/playlist/", include("playlist.urls")),
    path("api/download/", include("download.urls")),
    path("api/task/", include("task.urls")),
    path("api/appsettings/", include("appsettings.urls")),
    path("api/stats/", include("stats.urls")),
    path("api/user/", include("user.urls")),
    path("admin/", admin.site.urls),
]
