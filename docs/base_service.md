# Base Service Reference

This file documents the abstract service base classes used by the application.
It defines a shared service contract and helper methods that all services can reuse.

---

## Purpose

`services.base_service.BaseService` is the foundational class for all service objects.
It provides:

- a common interface via `execute()`
- error logging support
- simple in-memory result caching
- consistent service lifecycle methods

It is intentionally abstract so that subclasses implement real domain logic.

---

## Core classes

### `BaseService`

This class defines the service contract.

Key methods:

- `execute(*args, **kwargs) -> Any`
  - abstract method that subclasses must implement
- `_log_error(error_msg, context=None) -> None`
  - records internal error details
- `_cache_result(key, value, ttl=None) -> None`
  - stores a result in the service cache
- `_get_cached(key) -> Optional[Any]`
  - retrieves a cached result if available
- `get_errors() -> List[Dict]`
  - returns a copy of logged errors
- `clear_errors() -> None`
  - empties the error log
- `clear_cache() -> None`
  - empties internal cache

This class demonstrates:

- ABSTRACTION: defines what services do without specifying how
- POLYMORPHISM: different services implement `execute()` differently
- ENCAPSULATION: hides error and cache internals behind protected helpers

### `DataAccessService`

A specialized abstract subclass for data access operations.
It includes CRUD-style method signatures that concrete repositories or data services should implement.

Key methods:

- `get_all(*args, **kwargs) -> List[Any]`
- `get_by_id(entity_id) -> Optional[Any]`
- `create(data) -> Any`
- `update(entity_id, data) -> Optional[Any]`
- `delete(entity_id) -> bool`

This class demonstrates:

- INHERITANCE: reuses `BaseService` helpers
- POLYMORPHISM: each concrete data service provides its own storage logic

### `BusinessLogicService`

A specialized abstract subclass for domain and business logic services.
It provides shared validation and sanitation helpers.

Key methods:

- `validate_input(data, required_fields) -> bool`
  - ensures required keys are present and non-null
- `sanitize_data(data) -> Dict`
  - trims whitespace from string values and returns normalized data

This class demonstrates:

- INHERITANCE: reuses `BaseService` functionality
- ABSTRACTION: separates domain validation from concrete service behavior
- ENCAPSULATION: keeps helper logic inside the base class

---

## Why this matters

The base service layer makes it easy to add new services while keeping a consistent pattern.
All services share error handling, caching, and interface expectations.

Example:

```python
class MyService(BusinessLogicService):
    def execute(self, payload):
        if not self.validate_input(payload, ["name"]):
            return None
        data = self.sanitize_data(payload)
        return do_work(data)
```
