# Database Reference

This file documents the database schema and relationships.
It is written for people who know Python but may not know much SQL or databases.

---

## Overview

The application uses SQLAlchemy as an ORM (Object-Relational Mapper).
Think of SQLAlchemy as a Python layer that lets you write Python classes instead of raw SQL.

Database initialization:

```python
from database.db import db
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
```

Each Python model class automatically maps to a database table.

---

## Tables

### `users`

Stores user account information.

**Fields:**

- `user_id` (Integer, Primary Key): Unique user identifier
- `username` (String, Unique): Login username
- `password` (String): Hashed password
- `email` (String): User email
- `profile_picture` (String): URL to profile image
- `is_admin` (Boolean): Admin flag
- `country` (String): User country
- `created_at` (DateTime): Account creation timestamp
- `is_active` (Boolean): Whether user is currently logged in
- `last_active` (DateTime): Last activity timestamp

**Python class:**

```python
class User(UserMixin, db.Model):
    __tablename__ = "users"
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=False)
    last_active = db.Column(db.DateTime, nullable=True)
```

---

### `components`

Stores PC component data like CPUs, GPUs, RAM, etc.

**Fields:**

- `component_id` (Integer, Primary Key): Unique component identifier
- `name` (String): Component name (e.g., "Ryzen 7 5700X")
- `category` (String): Component type (CPU, GPU, RAM, PSU, etc.)
- `brand` (String): Manufacturer (e.g., AMD, Intel, NVIDIA)
- `external_id` (String, Unique): External reference ID
- `specs` (JSON): Component specifications as a dictionary
- `compatibility` (JSON): Compatibility metadata
- `price` (Float): Component price in Philippine Pesos (PHP)
- `performance_score` (Integer): Performance rating (0-100)
- `image_url` (String): Component image URL
- `description` (Text): Component description
- `links` (Relationship): Related store links

**Python class:**

```python
class Component(db.Model):
    __tablename__ = "components"
    component_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    specs = db.Column(db.JSON, nullable=False)
    compatibility = db.Column(db.JSON, nullable=False, default={})
    price = db.Column(db.Float, default=0, nullable=False)
    performance_score = db.Column(db.Integer, default=50, nullable=False)
```

**Example specs entry:**

```json
{
  "socket": "AM4",
  "cores": 8,
  "threads": 16,
  "tdp": 105,
  "base_clock_ghz": 3.6,
  "boost_clock_ghz": 4.6
}
```

---

### `builds`

Stores user PC build configurations.

**Fields:**

- `build_id` (Integer, Primary Key): Unique build identifier
- `user_id` (Integer): Owner of the build
- `name` (String): Build name (e.g., "Gaming PC 2024")
- `component_ids` (Text): JSON list of selected component IDs
- `total_price` (Float): Sum of all component prices
- `compatibility_status` (String): Build compatibility status
- `created_at` (DateTime): Build creation timestamp

**Python class:**

```python
class Build(db.Model):
    __tablename__ = "builds"
    build_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    name = db.Column(db.String(100))
    component_ids = db.Column(db.Text, default="[]")
    total_price = db.Column(db.Float, default=0)
    compatibility_status = db.Column(db.String(50))
```

**Example component_ids:**

```json
[1, 5, 12, 23, 45, 67]
```

---

### `activities`

Tracks user actions for the recent activity log.

**Fields:**

- `activity_id` (Integer, Primary Key): Unique activity identifier
- `user_id` (Integer): User who performed the action
- `action_type` (String): Type of action (e.g., build_created, profile_updated)
- `description` (String): Human-readable description
- `timestamp` (DateTime): When the action occurred

**Python class:**

```python
class Activity(db.Model):
    __tablename__ = "activities"
    activity_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    action_type = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
```

**Example activity:**

```python
Activity.log_activity(
    user_id=5,
    action_type="build_created",
    description="Created build: Gaming PC"
)
```

---

### `links`

Stores store URLs and prices for components.

**Fields:**

- `link_id` (Integer, Primary Key): Unique link identifier
- `component_id` (Integer, Foreign Key): Associated component
- `store` (String): Store name (e.g., "Lazada", "Shopee")
- `url` (String): Product URL
- `verified` (Boolean): Whether the link has been verified
- `price` (Float): Price at this store

**Python class:**

```python
class Link(db.Model):
    __tablename__ = "links"
    link_id = db.Column(db.Integer, primary_key=True)
    component_id = db.Column(db.Integer, db.ForeignKey('components.component_id'))
    store = db.Column(db.String(100))
    url = db.Column(db.String(500))
    price = db.Column(db.Float, default=0.0)
    component = db.relationship('Component', backref='links')
```

---

## Relationships

```
User (1) ──────→ (Many) Builds
User (1) ──────→ (Many) Activities
Component (1) ──→ (Many) Links
Build ──────────→ Components (via component_ids JSON)
```

---

## Common queries

### Get all components of a category

```python
cpus = Component.query.filter_by(category='CPU').all()
```

### Get a user's recent activities

```python
activities = Activity.get_recent_activities(user_id=5, limit=10)
```

### Get a user's builds

```python
builds = Build.query.filter_by(user_id=5).all()
```

### Get store prices for a component

```python
component = Component.query.get(component_id)
links = component.links  # All store entries
cheapest = min(links, key=lambda l: l.price)
```

---

## Why this design

- **JSON columns**: Used for flexible specs and compatibility metadata
- **Foreign keys**: Links components to store entries
- **Timestamps**: Track user activity and build history
- **Denormalization**: component_ids stored as JSON in Build for faster lookups
