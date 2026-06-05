# Pricing Service Reference

This file documents the pricing utilities used to calculate build totals and estimate store prices.
It supports budget checks, cheapest-store lookups, and build price breakdowns.

---

## Purpose

`services.pricing.pricing_service` provides pricing-related functions.
It is used by routes and UI flows that need build totals, store pricing, or budget analysis.

---

## Main functions

### `calculate_build_total(component_ids)`

Input:

- `component_ids`: list of component IDs

Output:

- `total`: sum of component prices
- `breakdown`: list of component price entries
- `count`: number of components

This function loads matched components and returns a simple price summary.

### `get_store_prices(component_id)`

Input:

- `component_id`: the ID of a component

Output:

- `cheapest`: cheapest store entry or `None`
- `stores`: ordered list of store price entries

This function reads `Link` records for a component and sorts them by price.

### `cheapest_build(component_ids)`

Input:

- `component_ids`: list of component IDs

Output:

- `total`: cheapest total cost across selected components
- `breakdown`: cheapest store entry for each component

This function chooses the lowest-price store link for each component,
falling back to the base component price when no store data exists.

### `price_budget_check(component_ids, budget)`

Input:

- `component_ids`: list of component IDs
- `budget`: integer budget limit

Output:

- `within_budget`: boolean
- `total`: current build total
- `budget`: original budget
- `difference`: amount over or under budget
- `message`: human-readable summary
- `savings_targets`: top 3 most expensive components when over budget

This function helps the UI determine whether a build is within the users budget.

---

## Why this matters

Pricing is a key part of build decision-making.
These helpers make it easy to calculate overall cost, compare store prices, and provide budget guidance.
