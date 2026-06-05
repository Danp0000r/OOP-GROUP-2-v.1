import functools
import hashlib
import json
import time

_cache_store = {}


def _normalize_value(value):
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, (list, tuple, set)):
        return [_normalize_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _normalize_value(value[key]) for key in sorted(value)}
    if hasattr(value, 'to_dict'):
        try:
            return _normalize_value(value.to_dict())
        except Exception:
            pass
    try:
        return repr(value)
    except Exception:
        return str(value)


def _make_cache_key(fn, args, kwargs):
    payload = {
        'func': f'{fn.__module__}.{fn.__name__}',
        'args': _normalize_value(args),
        'kwargs': _normalize_value(kwargs),
    }
    raw = json.dumps(payload, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
    return f"{payload['func']}:{hashlib.sha256(raw.encode('utf-8')).hexdigest()}"


def memoize(timeout=300):
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            key = _make_cache_key(fn, args, kwargs)
            now = time.time()
            entry = _cache_store.get(key)
            if entry is not None and entry['expires_at'] > now:
                return entry['value']
            value = fn(*args, **kwargs)
            _cache_store[key] = {
                'value': value,
                'expires_at': now + timeout,
            }
            return value

        wrapper.cache_key = lambda *a, **kw: _make_cache_key(fn, a, kw)
        return wrapper

    return decorator


def clear_cache(prefix=None):
    if prefix is None:
        _cache_store.clear()
        return
    keys_to_delete = [key for key in _cache_store if key.startswith(prefix)]
    for key in keys_to_delete:
        del _cache_store[key]


def get_cached_keys(prefix=None):
    if prefix is None:
        return list(_cache_store)
    return [key for key in _cache_store if key.startswith(prefix)]
