# Inheritance

Inheritance means a class can reuse behavior from a parent class, and specialized classes can extend or override that behavior.
This app uses inheritance in service classes, component wrappers, and spec objects.

## Inheritance in services

### `services.base_service.BaseService`
- base class for shared service helpers
- defines `_log_error()`, `_cache_result()`, `_get_cached()`, `get_errors()`, `clear_errors()`, and `clear_cache()`

### `services.base_service.BusinessLogicService`
- inherits from `BaseService`
- adds validation and sanitation helpers: `validate_input()` and `sanitize_data()`

### `services.activity.activity_service.ActivityService`
- inherits from `BusinessLogicService`
- uses inherited logging and cache helpers without reimplementing them

Example:

```python
class ActivityService(BusinessLogicService):
    def execute(self, activity_type, user_id, description):
        return self._create_activity(user_id, activity_type, description)
```

Because of inheritance, `ActivityService` can call `_cache_result()` and `_log_error()` directly.

## Inheritance in component models

### `models.component_specs.ComponentSpecs`
- base class for all spec wrappers
- provides common logic: `get()`, `raw`, `to_dict()`, `__getitem__`, `__contains__`

### Specialized specs
- `CPUSpecs`
- `GPUSpecs`
- `RAMSpecs`
- `StorageSpecs`
- `PSUSpecs`
- `MotherboardSpecs`
- `CoolingSpecs`
- `CaseSpecs`

Each subclass inherits the base dict behavior and adds domain-specific properties such as `cores`, `vram`, `wattage`, or `gpu_length_limit`.

### `models.base_component.BaseComponent`
- base wrapper for component objects
- defines `specs` property and `to_dict()` conversion

### Subclasses
- `CPUComponent`, `GPUComponent`, `RAMComponent`, etc.
- each subclass implements `_create_specs_object()` to return the right `ComponentSpecs` type

Example:

```python
component_class = ComponentFactory._COMPONENT_MAP["CPU"]
wrapper = component_class(raw_component)
print(wrapper.specs.socket)
```

## Inheritance in ORM models

The SQLAlchemy models also use inheritance from `db.Model`, for example:

- `models.user.User(UserMixin, db.Model)`
- `models.component.Component(db.Model)`
- `models.activity.Activity(db.Model)`

This lets them inherit ORM behavior from SQLAlchemy.

## Why it matters here

- avoids repeated code across services and models
- makes common behavior easy to share
- enables domain-specific specialization without rewriting basic helpers
- keeps the codebase more maintainable as new services or component types are added
