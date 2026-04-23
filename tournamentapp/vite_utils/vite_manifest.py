import json
from django.conf import settings

_manifest_cache = None


def get_vite_manifest():
    global _manifest_cache

    # In dev, always reload (no caching)
    if settings.DEBUG:
        manifest_path = settings.BASE_DIR / 'vite-manifest.json'
        with open(manifest_path, 'r') as f:
            return json.load(f)

    # In production, cache in memory
    if _manifest_cache is None:
        manifest_path = settings.BASE_DIR / 'vite-manifest.json'
        with open(manifest_path, 'r') as f:
            _manifest_cache = json.load(f)

    return _manifest_cache