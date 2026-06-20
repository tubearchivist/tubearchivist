"""OIDC authentication backend

Resolves OpenID Connect logins against the custom Account model
(USERNAME_FIELD = "name"), which the stock mozilla-django-oidc backend cannot
do on its own. Claim-to-value logic lives in user.src.oidc_claims so it stays
unit testable without Django.
"""

from django.conf import settings
from django.core.exceptions import SuspiciousOperation
from mozilla_django_oidc.auth import OIDCAuthenticationBackend
from user.src.oidc_claims import (
    admin_flags_from_groups,
    username_from_claims,
)


class TAOIDCBackend(OIDCAuthenticationBackend):
    """map OIDC claims onto TubeArchivist Account rows"""

    def _username_claim(self):
        return getattr(
            settings, "TA_OIDC_USERNAME_CLAIM", "preferred_username"
        )

    def verify_token(self, token, **kwargs):
        """pin the audience to our client id

        mozilla-django-oidc does not enforce `aud` by default; for a flow that
        can grant superuser, reject tokens minted for a different client.
        """
        payload = super().verify_token(token, **kwargs)
        audience = payload.get("aud")
        allowed = audience if isinstance(audience, list) else [audience]
        if not audience or self.OIDC_RP_CLIENT_ID not in allowed:
            raise SuspiciousOperation("OIDC token audience mismatch")

        return payload

    def verify_claims(self, claims):
        """a resolvable account name is the only hard requirement"""
        return bool(username_from_claims(claims, self._username_claim()))

    def filter_users_by_claims(self, claims):
        """match an existing account by exact name (the unique column)"""
        name = username_from_claims(claims, self._username_claim())
        if not name:
            return self.UserModel.objects.none()

        return self.UserModel.objects.filter(name=name)

    def create_user(self, claims):
        """provision a new account with an unusable password

        Instantiates the model directly to bypass AccountManager (which
        requires a password); set_unusable_password keeps the local
        ModelBackend from ever authenticating this SSO account.
        """
        name = username_from_claims(claims, self._username_claim())
        user = self.UserModel(name=name)
        user.set_unusable_password()
        self._apply_group_promotion(user, claims)
        user.save()

        return user

    def update_user(self, user, claims):
        """re-apply group based promotion on each login"""
        if self._apply_group_promotion(user, claims):
            user.save()

        return user

    def _apply_group_promotion(self, user, claims):
        """promote-only staff/superuser from the group claim

        Returns True when a flag changed so callers can avoid a needless save.
        Mirrors the LDAP backend: never demotes, so a manually granted local
        admin keeps access.
        """
        groups = claims.get(
            getattr(settings, "TA_OIDC_GROUPS_CLAIM", "groups"), []
        )
        is_staff, is_superuser = admin_flags_from_groups(
            groups,
            getattr(settings, "TA_OIDC_ADMIN_GROUP", ""),
            getattr(settings, "TA_OIDC_STAFF_GROUP", ""),
        )

        changed = False
        if is_staff and not user.is_staff:
            user.is_staff = True
            changed = True
        if is_superuser and not user.is_superuser:
            user.is_superuser = True
            changed = True

        return changed
