"""tests for PendingList functions"""

from datetime import datetime, timezone
from download.src.queue import PendingList


def test_returns_timestamp_if_present():
    video_data = {"timestamp": 1508457600}
    result = PendingList._PendingList__extract_published(video_data)
    assert result == 1508457600

def test_returns_iso_date_if_upload_date_present():
    video_data = {"upload_date": "20171020"}
    result = PendingList._PendingList__extract_published(video_data)

    dt = datetime.fromtimestamp(result, tz=timezone.utc)
    assert dt.year == 2017
    assert dt.month == 10
    assert dt.day == 20
    assert dt.hour == 0
    assert dt.minute == 0
    assert dt.second == 0

def test_returns_current_timestamp_if_no_date_info():
    video_data = {}

    before = int(datetime.now().timestamp())
    result = PendingList._PendingList__extract_published(video_data)
    after = int(datetime.now().timestamp())

    assert before <= result <= after