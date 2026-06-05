# Component Loader Reference

This file acts as the **database loader** for the compatibility system.

Its job is to retrieve all PC components from the database and convert them into a consistent format that the rest of the system can use.

> It does not decide whether parts are compatible.
> That responsibility belongs to the compatibility checker.

---

## What this file does

The loader is responsible for:

- reading component records from the database
- normalizing every component into a standard dictionary shape
- making the data available to the matcher and compatibility services

### Core flow

```text
Database
  ↓
ComponentLoader.load()
  ↓
Normalized Component List
  ↓
ComponentMatcher
  ↓
CompatibilityChecker
  ↓
PerformanceAnalyzer
```

---

## Importing caching

```python
from services.cache import memoize
```

`memoize` is a decorator that caches the function result in memory.

This makes repeated calls much faster and reduces database load.

## ComponentLoader.load()

```python
@memoize(timeout=600)
def load():
```

The `@memoize(timeout=600)` decorator means:

> Cache the return value for 600 seconds (10 minutes).

### Why caching matters

Without caching:

```text
User 1 → Database Query
User 2 → Database Query
User 3 → Database Query
...
User 100 → Database Query
```

With caching:

```text
First call → Database Query → Cache stored
Later calls → Return cached data → No database query
```

This makes the app faster and reduces server load.

### Cache expiration

The cache is valid for 10 minutes.

Example:

```text
12:00 PM → Cache filled
12:05 PM → Cached result used
12:08 PM → Cached result used
12:11 PM → Cache expired
12:11 PM → Reload database
```

---

## Loading components from the database

Inside `load()` the code imports the database model:

```python
from models.component import Component
```

That model represents the `components` table and its rows.

Then it loads all records:

```python
components = Component.query.all()
```

This asks the database for every saved component.

Example result:

```text
[
  CPU_1,
  CPU_2,
  GPU_1,
  GPU_2,
  RAM_1
]
```

Each item is a database object.

---

## Why the loader normalizes components

Database objects are useful, but the rest of the app expects plain dictionaries.

A normalized component looks like:

```json
{
  "id": "...",
  "name": "...",
  "category": "...",
  "brand": "...",
  "specs": {...},
  "compatibility": {...},
  "price": ..., 
  "performance_score": ...
}
```

This single structure keeps the matcher, checker, and analyzer working consistently.

---

## Example conversion

Database object:

```python
Component(
    id="cpu001",
    name="Ryzen 7 5700X",
    category="CPU",
    brand="AMD",
    price=10500
)
```

Normalized output:

```json
{
  "id": "cpu001",
  "name": "Ryzen 7 5700X",
  "category": "CPU",
  "brand": "AMD",
  "price": 10500
}
```

This is called **normalization**.

---

## Important fields

Each normalized component should include:

- `id` — unique identifier
- `name` — component name
- `category` — class such as `CPU`, `GPU`, `RAM`
- `brand` — manufacturer
- `specs` — technical details
- `compatibility` — compatibility metadata
- `price` — numeric cost
- `performance_score` — performance rating

### Why these fields matter

- `ComponentMatcher` reads `component["name"]`
- `CompatibilityChecker` reads `component["specs"]["socket"]`
- `PerformanceAnalyzer` reads `component["performance_score"]`

If each component used different keys, the system would become fragile.
Normalization guarantees a consistent contract.

---

## Error handling

The loader handles failures gracefully.

If an exception happens while loading components:

```python
try:
    ...
except Exception as e:
    print(f"Error loading components: {e}")
    return []
```

That means the app does not crash.
Instead, it returns an empty list and continues running.

---

## Why this file is important

This is the first step in the compatibility pipeline.

Without `component_loader.py`:

- the matcher would have no data to search
- the compatibility checker would have nothing to validate
- the performance analyzer would have no normalized inputs

So this loader is the foundation for the entire compatibility system.
