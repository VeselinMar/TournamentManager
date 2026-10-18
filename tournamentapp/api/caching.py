"""Cached, revalidatable responses for the public API (see tournamentapp/cache.py)."""
import json

from rest_framework import status
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

from tournamentapp.cache import get_or_build, public_etag


def _plain(data):
    """Turn serializer output into plain JSON types so it caches compactly and safely."""
    return json.loads(JSONRenderer().render(data))


def _matches_if_none_match(request, etag):
    header = request.META.get("HTTP_IF_NONE_MATCH", "")
    if not header:
        return False
    tags = {tag.strip().removeprefix("W/") for tag in header.split(",")}
    return etag in tags or "*" in tags


def cached_response(request, tournament, endpoint, builder):
    """
    Serve `builder()` for this tournament's current data version.

    Browsers revalidate on every poll (`no-cache` + ETag): unchanged data is
    answered with an empty 304, changed data with the fresh payload.
    """
    etag = public_etag(tournament, endpoint)
    headers = {"ETag": etag, "Cache-Control": "no-cache"}

    if _matches_if_none_match(request, etag):
        return Response(status=status.HTTP_304_NOT_MODIFIED, headers=headers)

    data = get_or_build(tournament, endpoint, lambda: _plain(builder()))
    return Response(data, headers=headers)
