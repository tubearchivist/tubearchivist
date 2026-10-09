"""
streaming abstraction consumed by MediaStreamView
partial implementation from
https://www.rfc-editor.org/rfc/rfc9110.html#section-14
"""

from collections.abc import AsyncIterator

import aiofiles
from django.http import StreamingHttpResponse


class RangeNotSatisfiable(Exception):
    """will raise 416"""


def _parse_range_header(range_header: str | None) -> tuple[str, str] | None:
    """Return the two members of a supported single byte range."""
    if not range_header:
        return None

    range_unit, separator, value = range_header.partition("=")
    if not separator or range_unit.lower() != "bytes":
        return None

    value = value.strip()

    # Multipart ranges are deliberately unsupported.
    if "," in value or value.count("-") != 1:
        return None

    first, last = value.split("-", 1)

    invalid_members = (
        (not first and not last)
        or (first and not first.isdecimal())
        or (last and not last.isdecimal())
    )
    if invalid_members:
        return None

    return first, last


def _resolve_range(first: str, last: str, file_size: int) -> tuple[int, int]:
    """Resolve parsed range members to inclusive file offsets."""
    if not first:
        # Suffix range: bytes=-500
        suffix_length = int(last)

        if suffix_length == 0 or file_size == 0:
            raise RangeNotSatisfiable

        start = max(0, file_size - suffix_length)
        end = file_size - 1

    else:
        start = int(first)

        if start >= file_size:
            raise RangeNotSatisfiable

        end = int(last) if last else file_size - 1

        if end < start:
            raise RangeNotSatisfiable

        end = min(end, file_size - 1)

    return start, end


def parse_range(
    range_header: str | None, file_size: int
) -> tuple[int, int] | None:
    """Parse a single HTTP byte range into inclusive file offsets."""
    parsed_range = _parse_range_header(range_header)
    if parsed_range is None:
        return None

    return _resolve_range(*parsed_range, file_size)


async def empty_stream() -> AsyncIterator[bytes]:
    """dummy an empty asynchronous response body"""
    for _ in range(0):
        yield b""


async def stream_file(path, start, end, chunk_size=256 * 1024):
    """Stream an inclusive byte range without buffering the entire file."""

    async with aiofiles.open(path, "rb") as file:

        await file.seek(start)
        remaining = end - start + 1

        while remaining > 0:
            chunk = await file.read(min(chunk_size, remaining))

            if not chunk:
                break

            remaining -= len(chunk)
            yield chunk


class RangedFileResponse(StreamingHttpResponse):
    """build the response"""

    def __init__(
        self,
        request,
        path,
        content_type="application/octet-stream",
    ):
        stat = path.stat()
        file_size = stat.st_size

        range_header = (
            request.headers.get("Range") if request.method == "GET" else None
        )

        # If-Range not implemented
        if request.headers.get("If-Range"):
            range_header = None

        try:
            byte_range = parse_range(range_header, file_size)
        except RangeNotSatisfiable:
            super().__init__(
                empty_stream(),
                status=416,
                content_type=content_type,
            )
            self["Content-Range"] = f"bytes */{file_size}"
            self["Content-Length"] = "0"
            self["Accept-Ranges"] = "bytes"
            return

        start, end = byte_range or (0, file_size - 1)
        content_length = max(0, end - start + 1)

        if request.method == "HEAD" or not content_length:
            streaming_content = empty_stream()
        else:
            streaming_content = stream_file(path, start, end)

        super().__init__(
            streaming_content,
            status=206 if byte_range else 200,
            content_type=content_type,
        )

        self["Accept-Ranges"] = "bytes"
        self["Content-Length"] = str(content_length)

        if byte_range:
            self["Content-Range"] = f"bytes {start}-{end}/{file_size}"
