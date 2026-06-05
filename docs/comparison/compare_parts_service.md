# Compare Parts Service Reference

This file documents the component comparison helper used for comparing individual parts.
It prepares comparison data for UI tables and export text.

---

## Purpose

`services.comparison.compare_parts_service.compare_components` builds a comparison payload for a list of selected component IDs.
It is used when users compare parts like CPUs, GPUs, RAM, or other component categories.

---

## Main function

### `compare_components(component_ids)`

Input:

- `component_ids`: list of component IDs to compare

Output:

- `items`: list of component dictionaries
- `all_keys`: sorted list of all spec keys across compared items
- `same_type`: boolean indicating whether all items share the same category
- `export_text`: a human-readable comparison summary

---

## How it works

### Step 1: load components

The function loads all matching components from the `Component` model.
It preserves the original selection order by mapping IDs back to the requested list.

### Step 2: prepare items

Each component is converted to a dictionary and augmented with a `cat` field for category.

### Step 3: collect spec keys

The function computes the union of all spec keys across the selected components.
This allows the comparison UI to render a full spec matrix.

### Step 4: determine same-type comparison

`same_type` is `True` only when every selected item shares the same `category`.

### Step 5: build export text

A simple plain-text export payload is generated for easy sharing or download.

---

## Caching

The function is decorated with `@memoize(timeout=300)`.
This caches comparison results for 5 minutes, which is useful when users repeatedly review the same part selection.

---

## Why this matters

This helper centralizes part comparison logic and ensures UI components receive a consistent payload.
It also keeps the comparison text generation in one place.
