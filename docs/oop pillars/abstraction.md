# Abstraction

Abstraction means exposing only what a caller needs and hiding the implementation details.
This codebase uses abstraction in models, repositories, and compatibility services.

## How abstraction is used in this app

- `services.component_repository.ComponentRepository`
  - public API: `get_all()`, `get_by_id()`, `get_by_category()`, `get_cpus()`, `get_ram_by_type()`
  - hides SQLAlchemy query building and conversion to `BaseComponent`
- `services.compatibility.compatibility_service.CompatibilityService`
  - public API: `evaluate_build(parts_input)`
  - hides component detection, grouping, compatibility rule checks, and performance analysis
- `models.base_component.BaseComponent`
  - exposes `to_dict()` and `specs` property
  - hides raw SQLAlchemy `Component` object access behind a stable wrapper
- `models.component_specs.ComponentSpecs`
  - exposes typed helpers like `get()`, `raw`, and `to_dict()` instead of raw dict access

## Useful abstraction examples

### Component repository

Instead of repeating SQLAlchemy queries across routes and services:

```python
repo = get_component_repository()
cpus = repo.get_cpus()
```

The caller does not need to know this uses:

```python
Component.query.filter_by(category="CPU").all()
```

### Compatibility service

The app calls:

```python
report = CompatibilityService.evaluate_build(parts_input)
```

without needing to know the implementation details for:

- `ComponentMatcher.detect_components()`
- `ComponentLoader.load()`
- `CompatibilityChecker.check()`
- `PerformanceAnalyzer.cpu_score()` and `gpu_score()`

### Component wrapper objects

`ComponentFactory.create(component_obj)` returns a category-specific wrapper, so callers can use:

```python
component = ComponentFactory.create(raw_component)
specs = component.specs
```

without depending on raw SQLAlchemy model shape.

## Why it matters here

- keeps the code easier to read and reason about
- centralizes database and compatibility logic
- lets the implementation change without changing callers
- reduces duplicate queries and repeated raw data handling
