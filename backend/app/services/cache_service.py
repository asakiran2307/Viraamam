"""Cache service — Redis-backed caching layer (Amazon/Flipkart style).

Instead of hitting the database on every request, frequently-read data
(categories, featured items, catalog pages) is cached in Redis with a TTL.

Cache is invalidated when an admin creates/updates/deletes any item or category.
"""
import json
import pickle
import hashlib
import redis
from flask import current_app

# TTLs (seconds)
TTL_CATEGORIES = 3600       # 1 hour  — categories rarely change
TTL_ITEMS_PAGE = 300        # 5 mins  — item catalog page
TTL_ITEM_DETAIL = 600       # 10 mins — single item detail
TTL_FEATURED = 600          # 10 mins — homepage featured items
TTL_ADS = 120               # 2 mins  — active ads


def _get_client():
    """Return a Redis client from the app config."""
    url = current_app.config.get("REDIS_URL", "redis://localhost:6379/0")
    try:
        client = redis.from_url(url, socket_connect_timeout=1, socket_timeout=1)
        client.ping()
        return client
    except Exception:
        return None  # Redis unavailable — fall through to DB


# ── Key builders ─────────────────────────────────────────────────────────────

def _key_categories():
    return "vc:categories"


def _key_featured():
    return "vc:featured"


def _key_ads():
    return "vc:ads"


def _key_item(item_id: int):
    return f"vc:item:{item_id}"


def _key_catalog(page: int, category_slug: str, search: str):
    raw = f"{page}|{category_slug}|{search}"
    h = hashlib.md5(raw.encode()).hexdigest()[:12]
    return f"vc:catalog:{h}"


# ── Generic helpers ───────────────────────────────────────────────────────────

def cache_get(key: str):
    """Return deserialized value or None if missing/unavailable."""
    r = _get_client()
    if not r:
        return None
    try:
        raw = r.get(key)
        return pickle.loads(raw) if raw else None
    except Exception:
        return None


def cache_set(key: str, value, ttl: int):
    """Serialize and store value with TTL. Silently fails if Redis is down."""
    r = _get_client()
    if not r:
        return
    try:
        r.setex(key, ttl, pickle.dumps(value))
    except Exception:
        pass


def cache_delete(*keys: str):
    """Delete one or more cache keys."""
    r = _get_client()
    if not r:
        return
    try:
        r.delete(*keys)
    except Exception:
        pass


def cache_delete_pattern(pattern: str):
    """Delete all keys matching a pattern (e.g. 'vc:catalog:*')."""
    r = _get_client()
    if not r:
        return
    try:
        keys = r.keys(pattern)
        if keys:
            r.delete(*keys)
    except Exception:
        pass


# ── Domain-level cache helpers ────────────────────────────────────────────────

def get_cached_categories():
    """Return cached categories list, or None to trigger a DB query."""
    return cache_get(_key_categories())


def set_cached_categories(categories):
    cache_set(_key_categories(), categories, TTL_CATEGORIES)


def get_cached_featured():
    return cache_get(_key_featured())


def set_cached_featured(items):
    cache_set(_key_featured(), items, TTL_FEATURED)


def get_cached_ads():
    return cache_get(_key_ads())


def set_cached_ads(ads):
    cache_set(_key_ads(), ads, TTL_ADS)


def get_cached_catalog(page, category_slug, search):
    return cache_get(_key_catalog(page, category_slug, search))


def set_cached_catalog(page, category_slug, search, data):
    cache_set(_key_catalog(page, category_slug, search), data, TTL_ITEMS_PAGE)


def get_cached_item(item_id):
    return cache_get(_key_item(item_id))


def set_cached_item(item_id, item):
    cache_set(_key_item(item_id), item, TTL_ITEM_DETAIL)


def invalidate_catalog_cache():
    """Call this whenever any item or category is added/updated/deleted."""
    cache_delete_pattern("vc:catalog:*")
    cache_delete(_key_featured())
    cache_delete(_key_categories())
    cache_delete(_key_ads())


def invalidate_item_cache(item_id: int):
    """Call this when a specific item is updated/deleted."""
    cache_delete(_key_item(item_id))
    invalidate_catalog_cache()
