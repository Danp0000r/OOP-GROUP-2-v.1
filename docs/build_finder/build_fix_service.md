# Build Fix Service Reference

This file documents the service that attempts to repair incompatible PC builds.
It works by evaluating build compatibility and applying low-impact substitutions.

---

## Purpose

`services.build_finder.build_fix_service.BuildFixService` is a helper for improving incompatible builds.
It does not guarantee a perfect solution,
but it attempts minimal changes to make a build compatible again.

The service is questionnaire-aware and uses compatibility analysis to guide fixes.

---

## Main flow

### `fix_build(parts, answers=None)`

Input:

- `parts`: a list of component dictionaries
- `answers`: optional questionnaire answers such as platform and budget

Output:

- `fixed`: whether the build is now compatible
- `components`: the updated component list
- `changes`: summary of replacements made
- `compatibility_report`: final compatibility report

Steps:

1. Evaluate the original build via `CompatibilityService.evaluate_build()`
2. If already compatible, return early
3. Build a working map of parts keyed by category/type
4. Attempt fixes for critical compatibility issues
5. Re-evaluate after each fix

---

## Fix strategies

The service includes several targeted repair functions:

### `fix_psu()`

- reads the recommended PSU wattage from the compatibility report
- selects a PSU with enough wattage
- replaces the PSU if the current one is inadequate

### `fix_ram()`

- determines the desired RAM type from motherboard or CPU compatibility metadata
- selects a matching RAM module, preferably cost-effective

### `fix_cooler_case()`

- checks cooler height vs case CPU cooler clearance
- switches to a smaller cooler if needed
- also handles radiator compatibility for AIO coolers and case support

### `fix_gpu_case()`

- checks GPU length vs case GPU clearance
- selects a shorter GPU with similar performance when available
- falls back to choosing a more spacious case if necessary

### `fix_socket()`

- compares CPU and motherboard socket metadata
- prefers replacing the motherboard to match the CPU
- uses JSON query filters when available, with fallback name-based searches

---

## Why this matters

This service helps users recover from incompatible build choices without manual component hunting.
It is especially useful for guided build workflows and questionnaire-driven recommendations.
