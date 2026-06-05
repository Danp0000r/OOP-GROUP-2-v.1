# Activity Service Reference

This file documents the activity logging service used for user actions.
It handles logging events such as profile updates, build creation, and compatibility checks.

---

## Purpose

`services.activity.activity_service.ActivityService` records user activity to the `Activity` model.
It is responsible for creating activity records and providing a simple service interface for the app.

The service uses `BusinessLogicService` as its base class,
which gives it shared validation and caching behavior.

---

## Main methods

### `execute(activity_type, user_id, description)`

The main entry point for the service.
It creates a new activity record with the provided type, user ID, and description.

### `_create_activity(user_id, activity_type, description)`

The protected helper that performs the actual database insert.
It logs an error internally if the activity cannot be created.

### Static convenience helpers

The service also exposes several static helper methods for common activity types:

- `log_profile_update(user_id, changes=None)`
- `log_password_change(user_id)`
- `log_build_created(user_id, build_name)`
- `log_build_updated(user_id, build_name)`
- `log_build_deleted(user_id, build_name)`
- `log_compatibility_check(user_id, build_name, status)`

These helpers build activity descriptions consistently and make caller code simpler.

---

## Why this matters

This service centralizes activity tracking logic.
Frontend or route handlers can call the service instead of interacting directly with the `Activity` model.
It also provides a single place to add audit or analytics logic later.
