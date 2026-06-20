"""OIDC settings for mozilla-django-oidc

Imported into config.settings when TA_LOGIN_AUTH_MODE is `oidc` or
`oidc_local`. All values are driven from TA_OIDC_* environment variables so no
provider details are baked into the image.
"""

from os import environ
from urllib.parse import urlparse


def _public_url():
    """first TA_HOST entry as a scheme://host[:port] base for redirect_uri"""
    hosts = (environ.get("TA_HOST") or "").split()
    if not hosts:
        return ""

    host = hosts[0].strip()
    if not host.startswith("http"):
        host = f"http://{host}"

    parsed = urlparse(host)
    netloc = parsed.netloc or parsed.path
    return f"{parsed.scheme}://{netloc}".rstrip("/")


def _env_bool(name, default):
    """parse a boolean-ish env var, falling back to default when unset"""
    value = environ.get(name)
    if value is None:
        return default

    return value.strip().lower() in ("1", "true", "yes", "on")


# Relying party (this app) credentials
OIDC_RP_CLIENT_ID = environ.get("TA_OIDC_CLIENT_ID")
OIDC_RP_CLIENT_SECRET = environ.get("TA_OIDC_CLIENT_SECRET")

# OpenID provider endpoints (Authentik etc.)
OIDC_OP_AUTHORIZATION_ENDPOINT = environ.get("TA_OIDC_AUTHORIZATION_ENDPOINT")
OIDC_OP_TOKEN_ENDPOINT = environ.get("TA_OIDC_TOKEN_ENDPOINT")
OIDC_OP_USER_ENDPOINT = environ.get("TA_OIDC_USER_ENDPOINT")
OIDC_OP_JWKS_ENDPOINT = environ.get("TA_OIDC_JWKS_ENDPOINT")

OIDC_RP_SIGN_ALGO = environ.get("TA_OIDC_SIGN_ALGO") or "RS256"
OIDC_RP_SCOPES = environ.get("TA_OIDC_SCOPES") or "openid profile email groups"

# auto-provision unknown users on first login (mozilla honours this)
OIDC_CREATE_USER = _env_bool("TA_OIDC_CREATE_USER", True)
# PKCE hardens the auth code in transit; TA sits behind proxies
OIDC_USE_PKCE = True
OIDC_PKCE_CODE_CHALLENGE_METHOD = "S256"

# where mozilla-django-oidc sends the browser after login
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/login/"

# public base URL used to build the OIDC redirect_uri (see oidc_views)
TA_OIDC_PUBLIC_URL = _public_url()

# read by user.src.oidc_auth and the public OIDC info endpoint
TA_OIDC_USERNAME_CLAIM = (
    environ.get("TA_OIDC_USERNAME_CLAIM") or "preferred_username"
)
TA_OIDC_GROUPS_CLAIM = environ.get("TA_OIDC_GROUPS_CLAIM") or "groups"
TA_OIDC_ADMIN_GROUP = environ.get("TA_OIDC_ADMIN_GROUP") or ""
TA_OIDC_STAFF_GROUP = environ.get("TA_OIDC_STAFF_GROUP") or ""
TA_OIDC_BUTTON_LABEL = environ.get("TA_OIDC_BUTTON_LABEL") or "Log in with SSO"
