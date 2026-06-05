# Encapsulation

Encapsulation means bundling data and behavior together while hiding implementation details behind a clean interface.
This repo uses encapsulation in service internals, component wrappers, and spec helpers.

## How encapsulation appears in this app

- `services.base_service.BaseService`
  - hides `_cache` and `_error_log`
  - exposes public methods: `get_errors()`, `clear_errors()`, `clear_cache()`
  - provides protected helpers `_log_error()`, `_cache_result()`, `_get_cached()` for subclasses
- `models.base_component.BaseComponent`
  - stores raw SQLAlchemy object in `_component`
  - caches parsed specs in `_specs`
  - exposes public `to_dict()` and `specs` while hiding internal access
- `models.component_specs.ComponentSpecs`
  - stores raw specs in `_specs`
  - exposes `get()`, `raw`, `to_dict()`, and property accessors like `wattage`, `capacity`
  - prevents direct external mutation of internal dict state

## More examples across files

### `ActivityService`

- public: `execute(activity_type, user_id, description)`
- hidden details: `_create_activity()` manages the database insert, caching, and error handling
- caller only sees the action, not the insert/rollback logic

### `BuildFixService`

- `fix_build(parts, answers=None)` is the public entry point
- internal helpers like `fix_psu()`, `fix_ram()`, `fix_gpu_case()`, and `fix_socket()` are local to the function
- internal state is kept in the `working` dictionary and is not exposed outside the fix routine

### `ComponentSpecs` and `BaseComponent`

- `ComponentSpecs` encapsulates component metadata
- `BaseComponent` encapsulates `Component` model access and normalization
- Example:

```python
specs = component.specs
print(specs.vram)
```

This is easier and safer than reading `component._component.specs["vram"]` directly.

## Why it matters here

- reduces accidental bugs from direct data mutation
- keeps implementation details in one place
- makes public APIs simpler to use
- supports safer reuse across services and models
