from django.conf import settings
from django.contrib.auth.middleware import PersistentRemoteUserMiddleware


class HttpRemoteUserMiddleware(PersistentRemoteUserMiddleware):
    """This class allows authentication via HTTP_REMOTE_USER which is set for
    example by certain SSO applications.
    """

    header = settings.TA_AUTH_PROXY_USERNAME_HEADER

    def process_request(self, request):
        """Only trust remote-user header from configured proxy IPs."""
        trusted_proxy_ips = getattr(settings, "TA_TRUSTED_PROXY_IPS", [])
        if isinstance(trusted_proxy_ips, str):
            trusted_proxy_ips = [
                ip.strip() for ip in trusted_proxy_ips.split(",") if ip.strip()
            ]

        if request.META.get("REMOTE_ADDR") not in trusted_proxy_ips:
            request.META.pop(self.header, None)

        return super().process_request(request)
