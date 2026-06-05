# Polymorphism

Polymorphism means different objects can be used through the same interface, while each object behaves in its own way.
This repo uses polymorphism in services, component wrappers, and spec objects.

## Polymorphism in services

### `execute()` method pattern
- `BaseService` defines `execute()` as an abstract method.
- concrete services like `ActivityService` implement it differently.
- this means code can treat multiple service classes similarly.

Example:

```python
service = ActivityService()
service.execute("build_created", user_id, "Created build")
```

A different service could also implement `execute()` for another domain.

## Polymorphism in component wrappers

### `ComponentFactory.create()`
- returns different wrapper objects based on component category
- each wrapper has the same public methods such as `to_dict()` and `specs`

Example:

```python
wrapper = ComponentFactory.create(raw_component)
print(wrapper.to_dict())
```

The same code works for CPU, GPU, RAM, or Case components.

### Component specs classes
- all specs classes inherit from `ComponentSpecs`
- but each subclass adds different properties
- same interface, different behavior

Example:

```python
if isinstance(specs, CPUSpecs):
    print(specs.cores)
elif isinstance(specs, GPUSpecs):
    print(specs.vram)
```

## Polymorphism in repository methods

### Shared query patterns
- `ComponentRepository.get_by_spec()` is a generic helper used by category-specific methods
- `get_cpus_by_socket()`, `get_ram_by_capacity()`, and `get_storage_by_type()` all reuse the same base behavior with different arguments

## Polymorphism in compatibility flow

- `CompatibilityService.evaluate_build()` accepts either a list of component dicts or string input
- `ComponentMatcher.get_component()` can return different component categories using the same matching process
- `CompatibilityChecker.check()` evaluates compatibility for CPUs, motherboards, RAM, PSUs, GPUs, cases, and coolers with the same output structure

## Why it matters here

- lets the app treat different components and services in a common way
- makes code extensible for new component types
- keeps public interfaces stable while behavior differs under the hood
- improves code reuse and consistency across the repo
