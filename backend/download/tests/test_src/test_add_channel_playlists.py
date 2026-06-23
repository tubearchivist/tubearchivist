"""tests for _add_channel_playlists handling of deleted channels"""

from unittest.mock import patch

import pytest
from download.src.yt_dlp_handler import DownloadPostProcess


class FakeChannelQueue:
    """minimal queue stand-in returning (channel_id, idx) pairs in order"""

    def __init__(self, items):
        self._items = list(items)

    def get_next(self):
        if not self._items:
            return None, None
        return self._items.pop(0)


class FakePlaylistQueue:
    """records add_list calls, returns nothing on get_next"""

    def __init__(self):
        self.added_lists: list[list] = []

    def get_next(self):
        return None, None

    def add_list(self, to_add):
        if to_add:
            self.added_lists.append(list(to_add))


@pytest.fixture
def handler():
    """handler with __init__ bypassed; doesn't touch config or task"""

    instance = DownloadPostProcess.__new__(DownloadPostProcess)
    instance.task = None
    return instance


def test_skips_channel_when_json_data_missing(handler, capsys):
    """#1103 regression: deleted ES channel must not raise AttributeError"""

    channel_id = "UCdeleted-channel-1"
    fake_channel_q = FakeChannelQueue([(channel_id, 0)])

    class FakeDeletedChannel:
        youtube_id = channel_id
        json_data = None

        def get_from_es(self):
            pass

        def get_overwrites(self):
            raise AssertionError(
                "get_overwrites must not be called when json_data is None"
            )

        def get_all_playlists(self):
            raise AssertionError(
                "get_all_playlists must not be called when json_data is None"
            )

    with patch(
        "download.src.yt_dlp_handler.RedisQueue",
        side_effect=[fake_channel_q, FakePlaylistQueue()],
    ), patch(
        "download.src.yt_dlp_handler.YoutubeChannel",
        return_value=FakeDeletedChannel(),
    ):
        handler._add_channel_playlists()

    captured = capsys.readouterr()
    assert "skip deleted channel" in captured.out
    assert channel_id in captured.out


def test_processes_channel_with_playlists_enabled(handler):
    """a live channel with index_playlists=true should add its playlists"""

    channel_id = "UClive-channel-2"
    fake_channel_q = FakeChannelQueue([(channel_id, 0)])
    fake_playlist_q = FakePlaylistQueue()

    class FakeLiveChannel:
        youtube_id = channel_id
        json_data = {"channel_overwrites": {"index_playlists": True}}
        all_playlists = [
            ("PLplaylistA", "Playlist A"),
            ("PLplaylistB", "Playlist B"),
        ]

        def get_from_es(self):
            pass

        def get_overwrites(self):
            return self.json_data["channel_overwrites"]

        def get_all_playlists(self):
            pass

    with patch(
        "download.src.yt_dlp_handler.RedisQueue",
        side_effect=[fake_channel_q, fake_playlist_q],
    ), patch(
        "download.src.yt_dlp_handler.YoutubeChannel",
        return_value=FakeLiveChannel(),
    ):
        handler._add_channel_playlists()

    assert fake_playlist_q.added_lists == [["PLplaylistA", "PLplaylistB"]]


def test_skips_channel_with_playlists_disabled(handler):
    """a live channel with index_playlists missing/false must add nothing"""

    channel_id = "UCquiet-channel-3"
    fake_channel_q = FakeChannelQueue([(channel_id, 0)])
    fake_playlist_q = FakePlaylistQueue()

    class FakeQuietChannel:
        youtube_id = channel_id
        json_data = {"channel_overwrites": {}}
        all_playlists = []

        def get_from_es(self):
            pass

        def get_overwrites(self):
            return self.json_data["channel_overwrites"]

        def get_all_playlists(self):
            pass

    with patch(
        "download.src.yt_dlp_handler.RedisQueue",
        side_effect=[fake_channel_q, fake_playlist_q],
    ), patch(
        "download.src.yt_dlp_handler.YoutubeChannel",
        return_value=FakeQuietChannel(),
    ):
        handler._add_channel_playlists()

    assert fake_playlist_q.added_lists == []
