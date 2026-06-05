# Component Repository Reference

This file documents the repository layer for component data access.
It centralizes database queries and hides SQLAlchemy details from the rest of the app.

---

## Purpose

`services.component_repository.ComponentRepository` is the data access layer for PC components.
It provides a clean API for retrieving components by category, name, specs, and price.

The repository implements the Repository pattern:

- ABSTRACTION: consumers do not need to know about SQLAlchemy query logic
- ENCAPSULATION: component access is centralized in one class
- POLYMORPHISM: category-specific retrieval methods share a consistent interface

---

## Main interface

### `get_all()`

Returns all components from the database.

### `get_by_id(component_id)`

Returns a single component by internal ID.

### `get_by_name(name)`

Returns a component that matches the exact `name`.

### `get_by_category(category)`

Returns components in a given category, such as `CPU`, `GPU`, or `RAM`.

### `search_by_name(search_term)`

Performs a substring search on component names.

### `search_by_brand(brand)`

Returns components filtered by brand.

### `get_by_price_range(min_price, max_price)`

Returns all components whose price falls between `min_price` and `max_price`.

### `get_by_spec(category, spec_key, spec_value)`

Returns components within a category whose specs match a given key/value pair.

---

## Category-specific convenience methods

The repository also exposes convenience methods for common categories:

- `get_cpus()`
- `get_cpus_by_socket(socket)`
- `get_cpus_by_cores(cores)`
- `get_gpus()`
- `get_gpus_by_vram(vram_gb)`
- `get_ram()`
- `get_ram_by_capacity(capacity_gb)`
- `get_ram_by_type(ram_type)`
- `get_storage()`
- `get_storage_by_type(storage_type)`
- `get_psus()`
- `get_psus_by_wattage(wattage)`
- `get_motherboards()`
- `get_motherboards_by_socket(socket)`
- `get_cooling()`
- `get_cases()`

These helpers simplify common lookup flows in the app.

---

## Singleton helper

### `get_component_repository()`

Returns a singleton repository instance.
This avoids repeated repository construction while preserving a consistent interface.

Example:

```python
from services.component_repository import get_component_repository
repo = get_component_repository()
cpus = repo.get_cpus()
```

---

## Why this matters

The component repository keeps database access predictable and maintainable.
If component storage changes later, only this layer needs to be updated.
