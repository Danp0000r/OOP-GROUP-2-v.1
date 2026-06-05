# Cache Reference

This file documents the in-memory caching helper used across the application.
It is not a full distributed cache, but a lightweight function-level cache for repeated requests.

---

## Purpose

`services.cache` provides utilities for memoizing expensive function calls and managing cached entries.
It is primarily used to speed up repeated queries and reduce database load.

---

## Core functions

### `memoize(timeout=300)`

A decorator that caches function results in memory for a limited time.

Behavior:

- generates a cache key based on the function module, name, args, and kwargs
- stores the return value along with an expiration timestamp
- returns cached results when still valid
- falls back to calling the wrapped function when the cache is absent or expired

Example usage:

```python
from services.cache import memoize

@memoize(timeout=600)
def load_components():
    return Component.query.all()
```

This is useful for functions that are deterministic and expensive to call repeatedly.

### `_normalize_value(value)`

Internal helper used by the cache key generator.
It converts values into cache-safe primitives,
including nested dicts, lists, tuples, sets, and objects with `to_dict()`.

### `_make_cache_key(fn, args, kwargs)`

Builds a stable cache key from:

- function module and name
- normalized positional args
- normalized keyword args

It uses SHA-256 hashing to keep keys compact.

### `clear_cache(prefix=None)`

Clears cached entries.

- `clear_cache()` removes all cached values
- `clear_cache(prefix)` removes entries whose keys start with the provided prefix

### `get_cached_keys(prefix=None)`

Returns a list of active cache keys,
optionally filtered by prefix.

---

## Why this matters

The cache helper reduces repeated work for functions such as component comparisons and lookups.
It is especially useful for read-heavy workloads in a request-driven web application.

Example:

```python
clear_cache("services.cache:my_module")
```
