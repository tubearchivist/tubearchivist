"""middleware"""

from django.conf import settings
from django.utils.deprecation import MiddlewareMixin


class StartTimeMiddleware(MiddlewareMixin):
    """add a start time header"""

    def __call__(self, request):
        response = self.get_response(request)
        response["X-Start-Timestamp"] = settings.TA_START
        return response
