"""tests for Pagination class to guard against ES max_result_window overflow.

regression test for issue #746: requesting a page that would push
``from + size`` past the 10000 hit boundary returned a 500 to the user.
the fix clamps ``page_from`` so the ES query fits in one request and
sets ``max_hits`` so the UI can flag the cap.
"""

from unittest.mock import patch

from common.src.index_generic import Pagination


class _StubRequest:
    """minimal request stand-in; only ``request.GET`` and ``request.user.id``
    are used by ``Pagination.__init__``."""

    def __init__(self, page):
        self._page = page
        self._user = type("_User", (), {"id": 1})()

    @property
    def user(self):
        return self._user

    class _GET:
        def __init__(self, page):
            self._page = str(page)

        def copy(self):
            return _StubRequest._GET(self._page)

        def get(self, key, default=None):
            if key == "page":
                return self._page
            return default

        def pop(self, key, default=None):
            return default

        def urlencode(self):
            return ""

    GET = property(lambda self: self._GET(self._page))


def _make_pagination(page, page_size):
    """build a Pagination without touching UserConfig / ES."""
    request = _StubRequest(page)
    with patch(
        "common.src.index_generic.UserConfig",
        return_value=type(
            "_UC", (), {"get_value": staticmethod(lambda *a, **k: page_size)}
        )(),
    ):
        return Pagination(request)


def test_first_page_within_window_is_unchanged():
    """page 1: from=0, no clamp, max_hits=False."""
    p = _make_pagination(page=1, page_size=150)
    assert p.pagination["page_from"] == 0
    assert p.pagination["page_size"] == 150
    assert p.pagination["max_hits"] is False


def test_middle_page_within_window_is_unchanged():
    """a normal mid-page is unaffected by the clamp."""
    p = _make_pagination(page=10, page_size=150)
    assert p.pagination["page_from"] == 9 * 150
    assert p.pagination["max_hits"] is False


def test_overflow_page_is_clamped():
    """the bug: page 67 of a 9981-video channel with page_size=150.
    raw from = 66 * 150 = 9900, + 150 = 10050 > 10000.
    expected: from is clamped to 10000 - 150 = 9850, max_hits=True.
    """
    p = _make_pagination(page=67, page_size=150)
    assert p.pagination["page_from"] == 9850
    assert p.pagination["page_size"] == 150
    assert p.pagination["max_hits"] is True


def test_overflow_page_at_exact_boundary_is_unchanged():
    """the last page that just fits stays unchanged (no clamp)."""
    # 10000 / 150 = 66.66..., so page 66 → from=9750, +150=9900, fits.
    p = _make_pagination(page=66, page_size=150)
    assert p.pagination["page_from"] == 9750
    assert p.pagination["max_hits"] is False


def test_overflow_with_different_page_size():
    """bug surfaces with any page_size; sanity-check a different value."""
    # 10000 / 50 = 200 exactly, so page 200 is fine, page 201 overflows
    p = _make_pagination(page=201, page_size=50)
    assert p.pagination["page_from"] == 10000 - 50
    assert p.pagination["max_hits"] is True


def test_max_result_window_is_documented_constant():
    """the constant should be exposed and equal to the ES default."""
    assert Pagination.MAX_RESULT_WINDOW == 10000
