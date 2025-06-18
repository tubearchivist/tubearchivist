from os import environ
import ldap
from django_auth_ldap.config import LDAPSearch

AUTH_LDAP_SERVER_URI = environ.get("TA_LDAP_SERVER_URI")

AUTH_LDAP_BIND_DN = environ.get("TA_LDAP_BIND_DN")

AUTH_LDAP_BIND_PASSWORD = environ.get("TA_LDAP_BIND_PASSWORD")

"""
Given Names are *_technically_* different from Personal names, as people
who change their names have different given names and personal names,
and they go by personal names. Additionally, "LastName" is actually
incorrect for many cultures, such as Korea, where the
family name comes first, and the personal name comes last.

But we all know people are going to try to guess at these, so still want
to include names that people will guess, hence using first/last as well.
"""

AUTH_LDAP_USER_ATTR_MAP_USERNAME = (
    environ.get("TA_LDAP_USER_ATTR_MAP_USERNAME")
    or environ.get("TA_LDAP_USER_ATTR_MAP_UID")
    or "uid"
)

AUTH_LDAP_USER_ATTR_MAP_PERSONALNAME = (
    environ.get("TA_LDAP_USER_ATTR_MAP_PERSONALNAME")
    or environ.get("TA_LDAP_USER_ATTR_MAP_FIRSTNAME")
    or environ.get("TA_LDAP_USER_ATTR_MAP_GIVENNAME")
    or "givenName"
)

AUTH_LDAP_USER_ATTR_MAP_SURNAME = (
    environ.get("TA_LDAP_USER_ATTR_MAP_SURNAME")
    or environ.get("TA_LDAP_USER_ATTR_MAP_LASTNAME")
    or environ.get("TA_LDAP_USER_ATTR_MAP_FAMILYNAME")
    or "sn"
)

AUTH_LDAP_USER_ATTR_MAP_EMAIL = (
    environ.get("TA_LDAP_USER_ATTR_MAP_EMAIL")
    or environ.get("TA_LDAP_USER_ATTR_MAP_MAIL")
    or "mail"
)

AUTH_LDAP_USER_BASE = environ.get("TA_LDAP_USER_BASE")

AUTH_LDAP_USER_FILTER = environ.get("TA_LDAP_USER_FILTER")

# pylint: disable=no-member
AUTH_LDAP_USER_SEARCH = LDAPSearch(
    AUTH_LDAP_USER_BASE,
    ldap.SCOPE_SUBTREE,
    "(&("
    + AUTH_LDAP_USER_ATTR_MAP_USERNAME
    + "=%(user)s)"
    + AUTH_LDAP_USER_FILTER
    + ")",
)

AUTH_LDAP_USER_ATTR_MAP = {
    "username": AUTH_LDAP_USER_ATTR_MAP_USERNAME,
    "first_name": AUTH_LDAP_USER_ATTR_MAP_PERSONALNAME,
    "last_name": AUTH_LDAP_USER_ATTR_MAP_SURNAME,
    "email": AUTH_LDAP_USER_ATTR_MAP_EMAIL,
}

if bool(environ.get("TA_LDAP_DISABLE_CERT_CHECK")):
    # pylint: disable=global-at-module-level
    global AUTH_LDAP_GLOBAL_OPTIONS
    AUTH_LDAP_GLOBAL_OPTIONS = {
        ldap.OPT_X_TLS_REQUIRE_CERT: ldap.OPT_X_TLS_NEVER,
    }
