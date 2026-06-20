"""pure helpers for mapping OIDC claims onto TubeArchivist accounts

Kept import-free (no Django, no mozilla_django_oidc) so the mapping logic can
be unit tested without bootstrapping the app. The Django glue lives in
user.src.oidc_auth.
"""


def username_from_claims(claims, claim_name="preferred_username"):
    """resolve the account name from OIDC claims

    Uses the configured claim, falling back only to the stable ``sub`` so an
    identity never silently resolves to a different, reassignable claim
    (e.g. email) between logins.
    """
    for key in (claim_name, "sub"):
        value = claims.get(key)
        if value:
            return str(value)

    return ""


def admin_flags_from_groups(groups, admin_group, staff_group):
    """map OIDC group membership to (is_staff, is_superuser)

    Promote-only, mirroring the LDAP backend: belonging to admin_group grants
    superuser (which implies staff); staff_group grants staff. Empty group
    names disable that tier. Never demotes here - callers decide that.
    """
    groups = groups or []
    is_superuser = bool(admin_group) and admin_group in groups
    is_staff = is_superuser or (bool(staff_group) and staff_group in groups)

    return is_staff, is_superuser
