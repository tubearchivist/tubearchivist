"""Serve the built frontend and collected Django static files."""

import mimetypes
from pathlib import Path

from django.conf import settings
from django.http import Http404, HttpResponse
from django.views.decorators.http import require_safe

FRONTEND_ROOT = Path(settings.BASE_DIR, "static")
STATIC_ROOT = Path(settings.STATIC_ROOT)


def _serve_file(root: Path, relative_path: str, cache_control: str):
    """Read a file below root without allowing path traversal."""
    root = root.resolve()
    file_path = (root / relative_path).resolve()
    if not file_path.is_relative_to(root) or not file_path.is_file():
        raise Http404

    content_type, content_encoding = mimetypes.guess_type(file_path.name)
    response = HttpResponse(
        file_path.read_bytes(),
        content_type=content_type or "application/octet-stream",
    )
    response["Cache-Control"] = cache_control
    if content_encoding:
        response["Content-Encoding"] = content_encoding

    return response


@require_safe
def frontend_asset(_request, asset_path: str, directory: str):
    """Serve a file from one of Vite's public output directories."""
    cache_control = "public, max-age=3600"
    if directory == "assets":
        cache_control = "public, max-age=31536000, immutable"
    elif directory == "css":
        cache_control = "no-cache, must-revalidate"
    return _serve_file(
        FRONTEND_ROOT, f"{directory}/{asset_path}", cache_control
    )


@require_safe
def django_static(_request, asset_path: str):
    """Serve collected Django assets, including the admin frontend."""
    return _serve_file(STATIC_ROOT, asset_path, "public, max-age=3600")


@require_safe
def frontend_index(_request):
    """Serve the Vite entry point for root and client-side routes."""
    response = _serve_file(
        FRONTEND_ROOT,
        "index.html",
        "no-store, no-cache, must-revalidate",
    )
    response["Pragma"] = "no-cache"
    response["Expires"] = "0"
    return response
