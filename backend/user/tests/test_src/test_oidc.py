"""test OIDC claim and group mapping helpers"""

import pytest
from user.src.oidc_claims import admin_flags_from_groups, username_from_claims


@pytest.mark.parametrize(
    "claims,claim_name,expected",
    [
        ({"preferred_username": "alice"}, "preferred_username", "alice"),
        # email is NOT a fallback - only the configured claim then sub
        ({"email": "bob@example.com"}, "preferred_username", ""),
        ({"sub": "abc-123"}, "preferred_username", "abc-123"),
        ({"sub": "s-1", "email": "x@y.z"}, "preferred_username", "s-1"),
        ({"name": "carol"}, "name", "carol"),
        ({}, "preferred_username", ""),
        ({"preferred_username": ""}, "preferred_username", ""),
    ],
)
def test_username_from_claims(claims, claim_name, expected):
    """resolve the account name from claims with sensible fallbacks"""
    assert username_from_claims(claims, claim_name) == expected


def test_username_prefers_configured_claim():
    """the configured claim wins over the default chain"""
    claims = {"preferred_username": "alice", "email": "alice@example.com"}
    assert username_from_claims(claims, "email") == "alice@example.com"


@pytest.mark.parametrize(
    "groups,admin_group,staff_group,expected",
    [
        (["ta-admins"], "ta-admins", "ta-staff", (True, True)),
        (["ta-staff"], "ta-admins", "ta-staff", (True, False)),
        (["other"], "ta-admins", "ta-staff", (False, False)),
        ([], "ta-admins", "ta-staff", (False, False)),
        (None, "ta-admins", "ta-staff", (False, False)),
        (["ta-admins"], "", "", (False, False)),
        (["ta-admins", "ta-staff"], "ta-admins", "ta-staff", (True, True)),
    ],
)
def test_admin_flags_from_groups(groups, admin_group, staff_group, expected):
    """map OIDC groups to (is_staff, is_superuser); admin implies staff"""
    assert (
        admin_flags_from_groups(groups, admin_group, staff_group) == expected
    )
