#!/usr/bin/env python
"""
Database initialization script.
Run this to create or recreate all database tables.
"""

import os
from __init__ import create_app
from database.db import db

def init_database():
    """Initialize the database by creating all tables."""
    app = create_app()
    
    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        print("✓ Database tables created successfully!")
        print("\nTables created:")
        print("  - users")
        print("  - builds")
        print("  - activities")
        print("  - components (and related tables)")
        print("  - links")
        
if __name__ == "__main__":
    init_database()
