"""
Versioned caching for the public tournament pages.

How it works
------------
* Every tournament has a `cache_version` number.
* Public API responses are cached under
  ``public:<tournament id>:<cache_version>:<endpoint>``.
* Any change to data shown on the public page bumps `cache_version`
  (see `signals.py`). New requests then use a new key, so stale entries are
  never read again and simply expire.

Why this is safe with several worker processes
----------------------------------------------
The version lives in the database, which all workers share, and is read on
every public request (one small query). Each worker may keep its own copy of
a response in its local cache, but always under the current version, so no
worker can serve outdated data. Bumps run inside the same database
transaction as the change, so readers never see the new version with old
data or the other way round.

Bulk operations (schedule generation, imports, bracket refresh) wrap their
work in `batched_invalidation()` so hundreds of saves cause a single bump.
"""
import threading
from contextlib import contextmanager

from django.conf import settings
from django.core.cache import cache
from django.db.models import F

PUBLIC_CACHE_TIMEOUT = 60 * 60  # stale versions are never read; this only frees memory

_state = threading.local()


# ---------------------------------------------------------------------------
# Invalidation
# ---------------------------------------------------------------------------

def _bump(tournament_ids):
    from .models import Tournament
    ids = {pk for pk in tournament_ids if pk is not None}
    if ids:
        Tournament.objects.filter(pk__in=ids).update(cache_version=F('cache_version') + 1)


def invalidate(tournament_id):
    """Mark a tournament's public data as changed."""
    if tournament_id is None:
        return
    if getattr(_state, 'depth', 0):
        _state.pending.add(tournament_id)
    else:
        _bump([tournament_id])


@contextmanager
def batched_invalidation():
    """Collect invalidations inside the block and bump each tournament once at the end."""
    depth = getattr(_state, 'depth', 0)
    if depth == 0:
        _state.pending = set()
    _state.depth = depth + 1
    try:
        yield
    except BaseException:
        _state.depth -= 1
        if _state.depth == 0:
            pending, _state.pending = _state.pending, set()
            try:
                _bump(pending)
            except Exception:
                # The transaction is already broken; never hide the original error.
                pass
        raise
    else:
        _state.depth -= 1
        if _state.depth == 0:
            pending, _state.pending = _state.pending, set()
            _bump(pending)


# ---------------------------------------------------------------------------
# Reading
# ---------------------------------------------------------------------------

def public_cache_key(tournament, endpoint):
    return f"public:{tournament.pk}:{tournament.cache_version}:{endpoint}"


def public_etag(tournament, endpoint):
    """Changes with the data version and with every deploy (response shapes may change)."""
    return f'"{settings.CODE_VERSION}-{tournament.pk}-{tournament.cache_version}-{endpoint}"'


def get_or_build(tournament, endpoint, builder):
    """Return the cached payload for this tournament version, building it on a miss."""
    key = public_cache_key(tournament, endpoint)
    data = cache.get(key)
    if data is None:
        data = builder()
        cache.set(key, data, PUBLIC_CACHE_TIMEOUT)
    return data
