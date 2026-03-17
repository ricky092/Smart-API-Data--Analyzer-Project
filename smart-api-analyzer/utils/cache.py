"""Simple TTL cache using functools + time to avoid redundant API calls."""

import time
import functools
from typing import Callable

_cache: dict = {}


def ttl_cache(seconds: int = 300):
    """Decorator that caches function results for `seconds` duration."""
    def decorator(fn: Callable):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            key = (fn.__name__, args, tuple(sorted(kwargs.items())))
            now = time.time()
            if key in _cache:
                result, ts = _cache[key]
                if now - ts < seconds:
                    return result
            result = fn(*args, **kwargs)
            _cache[key] = (result, now)
            return result
        return wrapper
    return decorator


def clear_cache():
    _cache.clear()
