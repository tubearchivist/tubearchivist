"""middleware"""

from django.conf import settings


class StartTimeMiddleware:
    """set start time header"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response["X-Start-Timestamp"] = settings.TA_START
        return response
