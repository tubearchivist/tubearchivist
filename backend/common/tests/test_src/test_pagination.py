"""tests for pagination and the Elasticsearch result window"""

# pylint: disable=redefined-outer-name

from unittest.mock import Mock

import pytest
from common.src.index_generic import Pagination
from django.http import QueryDict
from rest_framework.exceptions import ValidationError


@pytest.fixture
def make_pagination(monkeypatch):
    """build pagination without loading persisted user settings"""
    monkeypatch.setattr(
        "django.http.request.settings",
        Mock(DATA_UPLOAD_MAX_NUMBER_FIELDS=1000),
    )

    def build(page, page_size):
        config = Mock()
        config.return_value.get_value.return_value = page_size
        monkeypatch.setattr("common.src.index_generic.UserConfig", config)
        request = Mock()
        request.GET = QueryDict(f"page={page}&channel=test", encoding="utf-8")
        return Pagination(request)

    return build


@pytest.mark.parametrize(
    "page,expected_from",
    [(0, 0), (1, 0), (2, 25), (4, 75)],
)
def test_page_offset(make_pagination, page, expected_from):
    """first-page aliases and later offsets preserve other query parameters"""
    result = make_pagination(page, 25).pagination
    assert result["page_from"] == expected_from
    assert result["page_size"] == 25
    assert result["params"] == "channel=test"


@pytest.mark.parametrize(
    "page,total,last_page,next_pages",
    [
        (0, 0, False, []),
        (1, 25, False, []),
        (1, 101, 5, [2, 3, 4]),
        (5, 101, False, []),
    ],
)
def test_navigation(make_pagination, page, total, last_page, next_pages):
    """empty, single-page, and multi-page results expose valid links"""
    pagination = make_pagination(page, 25)
    pagination.validate(total)
    assert pagination.pagination["last_page"] == last_page
    assert pagination.pagination["next_pages"] == next_pages
    assert pagination.pagination["total_hits"] == total
    assert pagination.pagination["max_hits"] is False


@pytest.mark.parametrize(
    "total,page_size,last_page",
    [
        (9981, 150, 67),
        (9990, 24, 417),
        (10000, 200, 50),
        (10000, 150, 67),
    ],
)
def test_result_window_boundary(make_pagination, total, page_size, last_page):
    """keep the final page accessible without exceeding the result window"""
    pagination = make_pagination(1, page_size)
    pagination.validate(total)
    assert pagination.pagination["last_page"] == last_page
    assert pagination.pagination["max_hits"] == (total >= 10000)

    final_page = make_pagination(last_page, page_size).pagination
    assert final_page["page_from"] == (last_page - 1) * page_size
    assert final_page["page_size"] > 0
    end = final_page["page_from"] + final_page["page_size"]
    assert total <= end <= 10000


@pytest.mark.parametrize("page,page_size", [(51, 200), (68, 150)])
def test_page_beyond_result_window(make_pagination, page, page_size):
    """reject offsets outside the result window before querying"""
    with pytest.raises(ValidationError):
        make_pagination(page, page_size)
