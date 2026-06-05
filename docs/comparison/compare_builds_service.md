# Compare Builds Service Reference

This file documents the service that prepares build comparison payloads.
It is used when users compare saved builds side-by-side.

---

## Purpose

`services.comparison.compare_builds_service.compare_builds` creates a structured summary of selected builds.
It is responsible for retrieving build metadata, component lists, and compatibility reports.

---

## Main function

### `compare_builds(build_ids, user_id)`

Input:

- `build_ids`: list of saved build IDs to compare
- `user_id`: the owner of the builds

Output:

- `items`: list of build summary objects

Each build summary includes:

- `id`
- `name`
- `created_at`
- `part_count`
- `total_price`
- `compatibility_status`
- `components`
- `compatibility_report`

---

## How it works

### Step 1: load saved builds

Builds are loaded from the `Build` model.
Only builds belonging to the provided `user_id` are included.

### Step 2: parse component IDs

Each build may store component IDs in JSON or list form.
The helper `parse_component_ids()` normalizes this input into a Python list.

### Step 3: load component details

The service loads component rows from the `Component` table,
sorts them by category and name, and transforms them into payload rows.

### Step 4: evaluate compatibility

For each build, the service calls `CompatibilityService.evaluate_build()` using the selected components.
The compatibility report is included in the returned payload.

---

## Why this matters

This service makes comparing builds easy and consistent.
It avoids duplicating build-loading logic in multiple routes or views,
and ensures that each comparison includes both pricing and compatibility context.
