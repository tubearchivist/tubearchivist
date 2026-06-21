"""test ManualImport.run fallback when YT metadata fetch fails.

covers issue #1133: importing a private video (or hitting a bot block / no
internet) used to raise an uncaught KeyError/ConnectionError and abort the
entire import task. After the fix, the run() method catches those and falls
back to embedded metadata via IndexFromEmbed, mirroring the existing
ValueError fallback shape.
"""

from unittest.mock import patch

import pytest

from appsettings.src.manual import ManualImport


SAMPLE_VIDEO = {
    "media": "/cache/import/dQw4w9WgXcQ.mp4",
    "video_id": "dQw4w9WgXcQ",
    "metadata": False,
    "thumb": False,
    "subtitle": [],
}

EMBED_JSON_DATA = {"video_id": "dQw4w9WgXcQ", "media_url": "channel/test.mp4"}

CONFIG = {"downloads": {"integrate_ryd": False, "integrate_sponsorblock": False}}


def _make_import(ignore_error: bool = False) -> ManualImport:
    return ManualImport(
        SAMPLE_VIDEO,
        config=CONFIG,
        ignore_error=ignore_error,
        prefer_local=False,
    )


def _run_with_fallback(index_error, embed_return):
    """drive the run() path with both error types and assert fallback fires."""
    with (
        patch.object(ManualImport, "index_metadata", side_effect=index_error),
        patch("appsettings.src.manual.IndexFromEmbed") as mock_embed,
        patch.object(ManualImport, "_move_to_archive"),
        patch.object(ManualImport, "_cleanup"),
        patch("appsettings.src.manual.Comments"),
        patch("appsettings.src.manual.YoutubeVideo"),
    ):
        mock_embed.return_value.run_index.return_value = embed_return
        _make_import().run()
        return mock_embed


def test_keyerror_falls_back_to_embedded():
    """issue #1133: KeyError on missing 'id' must not abort the task."""
    mock_embed = _run_with_fallback(KeyError("id"), EMBED_JSON_DATA)

    mock_embed.assert_called_once_with(
        SAMPLE_VIDEO["media"], use_user_conf=False, config=CONFIG
    )
    mock_embed.return_value.run_index.assert_called_once()


def test_connection_error_falls_back_to_embedded():
    """no-internet path: ConnectionError from yt_dlp must trigger fallback."""
    mock_embed = _run_with_fallback(
        ConnectionError("lost the internet, abort!"), EMBED_JSON_DATA
    )

    mock_embed.assert_called_once()


def test_value_error_still_falls_back_to_embedded():
    """regression: the pre-existing ValueError path still works."""
    mock_embed = _run_with_fallback(
        ValueError("manual import failed"), EMBED_JSON_DATA
    )

    mock_embed.assert_called_once()


def test_keyerror_with_no_embed_and_strict_mode_raises():
    """strict mode (ignore_error=False) must still raise when both paths fail."""
    with (
        patch.object(ManualImport, "index_metadata", side_effect=KeyError("id")),
        patch("appsettings.src.manual.IndexFromEmbed") as mock_embed,
    ):
        mock_embed.return_value.run_index.return_value = None
        with pytest.raises(ValueError):
            _make_import(ignore_error=False).run()


def test_keyerror_with_no_embed_and_lenient_mode_silent():
    """ignore_error=True must swallow the failure when fallback also empty."""
    with (
        patch.object(ManualImport, "index_metadata", side_effect=KeyError("id")),
        patch("appsettings.src.manual.IndexFromEmbed") as mock_embed,
    ):
        mock_embed.return_value.run_index.return_value = None
        _make_import(ignore_error=True).run()
