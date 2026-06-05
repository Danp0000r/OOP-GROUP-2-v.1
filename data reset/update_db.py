import datetime
import json
import os
import sqlite3
import sys
import logging
from pathlib import Path

# Root project directory
ROOT_DIR = os.path.dirname(
    os.path.dirname(__file__)
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def ensure_users_created_at(users_db_path):
    if not os.path.exists(users_db_path):
        return
    try:
        conn = sqlite3.connect(users_db_path)
        cur = conn.cursor()
        columns = [row[1] for row in cur.execute("PRAGMA table_info(users)").fetchall()]
        if "created_at" not in columns:
            cur.execute(
                "ALTER TABLE users ADD COLUMN created_at DATETIME DEFAULT (datetime('now'))"
            )
            conn.commit()
    except Exception:
        pass
    finally:
        try:
            conn.close()
        except Exception:
            pass

# Allow root imports
sys.path.insert(0, ROOT_DIR)

from __init__ import create_app

from database.db import db

from models.component import Component
from models.link import Link
from models.user import User
from models.build import Build


def load_json_file(path):

    if not os.path.exists(path):

        raise FileNotFoundError(
            f"Required data file not found: {path}"
        )

    with open(path, "r", encoding="utf-8") as file:

        data = json.load(file)

    return data if data else []


def update_database():

    app = create_app()

    with app.app_context():

        # If an old components database exists with an outdated schema,
        # remove it so `create_all()` can create the correct tables.
        # Try common locations for the components sqlite database
        instance_dir = os.path.join(ROOT_DIR, "instance")
        os.makedirs(instance_dir, exist_ok=True)

        possible_paths = [
            os.path.join(ROOT_DIR, "components.db"),
            os.path.join(instance_dir, "components.db"),
        ]

        for components_db_path in possible_paths:
            try:
                if os.path.exists(components_db_path):
                    os.remove(components_db_path)
            except Exception:
                # If removal fails, continue to other paths
                pass

        # Recreate the components bind tables explicitly using the current model schema.
        engine = db.engines["components"]
        Link.__table__.drop(engine, checkfirst=True)
        Component.__table__.drop(engine, checkfirst=True)
        db.metadata.create_all(bind=engine, tables=[Component.__table__, Link.__table__])

        # Also recreate main DB tables (users/builds) in the default bind (users.db)
        # Remove any existing users.db to ensure schema matches models
        users_db_path = os.path.join(instance_dir, "users.db")
        try:
            if os.path.exists(users_db_path):
                os.remove(users_db_path)
        except Exception:
            ensure_users_created_at(users_db_path)

        # In case the old file persisted or the table already existed,
        # drop old tables before recreating the schema.
        try:
            User.__table__.drop(db.engine, checkfirst=True)
            Build.__table__.drop(db.engine, checkfirst=True)
        except Exception:
            pass

        # Create users/builds tables
        db.metadata.create_all(bind=db.engine, tables=[User.__table__, Build.__table__])
        ensure_users_created_at(users_db_path)

        # Clear old data
        db.session.query(Link).delete()
        db.session.query(Component).delete()

        db.session.commit()

        # JSON file paths
        components_path = os.path.join(
            ROOT_DIR,
            "data reset",
            "components.json"
        )

        links_path = os.path.join(
            ROOT_DIR,
            "data reset",
            "links.json"
        )

        # Load components
        components = load_json_file(
            components_path
        )

        for item in components:

            specs = dict(item.get("specs", {}))
            if "rgb" in item:
                specs["rgb"] = item["rgb"]

            # Construct a readable description from specs when no explicit description provided
            raw_description = item.get("description", "") or ""
            if not raw_description:
                parts = []
                for k, v in specs.items():
                    try:
                        # Represent lists/dicts as JSON-like strings, booleans as lowercase
                        if isinstance(v, (list, dict)):
                            val = json.dumps(v, ensure_ascii=False)
                        elif isinstance(v, bool):
                            val = str(v).lower()
                        else:
                            val = str(v)
                    except Exception:
                        val = str(v)
                    parts.append(f"{k}: {val}")
                raw_description = ", ".join(parts)

            component = Component(

                external_id=item.get("id"),

                name=item.get("name"),

                category=item.get("category"),

                brand=item.get("brand"),

                specs=specs,

                compatibility=item.get("compatibility", {}),

                # Components no longer carry a default price in components.json.
                # Price will be derived from associated links (lowest link price).
                price=0,

                performance_score=item.get(
                    "performance_score",
                    50
                ),

                image_url=item.get(
                    "image_url",
                    ""
                ),
                description=raw_description
            )

            db.session.add(component)

        db.session.commit()

        # Load links
        links = load_json_file(links_path)

        unmatched = 0
        added = 0
        for item in links:
            name = item.get("component_name") or item.get("name") or ""

            # Try exact name match first
            component = Component.query.filter_by(name=name).first()

            # Then try external_id match
            if not component:
                component = Component.query.filter_by(external_id=name).first()

            # Fallback: case-insensitive contains match
            if not component and name:
                component = Component.query.filter(Component.name.ilike(f"%{name}%")).first()

            if not component:
                unmatched += 1
                continue

            link = Link(
                component_id=component.component_id,
                store=item.get("store") or item.get("store_name") or "",
                url=item.get("url") or item.get("link") or "",
                price=float(item.get("price", 0) or 0),
                verified=bool(item.get("verified", False)),
            )

            try:
                db.session.add(link)
                added += 1
            except Exception:
                # ignore bad items but continue
                continue

        db.session.commit()

        # Recompute component prices from links: default price = lowest link price (if any)
        all_components = Component.query.all()
        for comp in all_components:
            link_rows = Link.query.filter_by(component_id=comp.component_id).all()
            if link_rows:
                prices = [float(l.price or 0) for l in link_rows if (l.price is not None)]
                comp.price = min(prices) if prices else 0
            else:
                comp.price = 0

        db.session.commit()

        # Load users and their builds from JSON
        users_path = os.path.join(ROOT_DIR, "data reset", "users.json")
        try:
            users = load_json_file(users_path)
        except FileNotFoundError:
            users = []

        users_added = 0
        builds_added = 0
        for u in users:
            try:
                user = User(
                    username=u.get("username"),
                    email=u.get("email"),
                )
                # set password (hashed)
                user.set_password(u.get("password", ""))
                user.is_admin = bool(u.get("is_admin", False))
                db.session.add(user)
                db.session.commit()
                users_added += 1

                # add builds for user
                for b in u.get("builds", []):
                    comp_ids = b.get("component_ids", []) or []
                    # compute total price from component prices
                    comps = Component.query.filter(Component.component_id.in_(comp_ids)).all() if comp_ids else []
                    total = sum([float(c.price or 0) for c in comps])
                    build = Build(
                        user_id=user.user_id,
                        name=b.get("name", "My Build"),
                        component_ids=json.dumps(comp_ids),
                        total_price=total,
                        compatibility_status=b.get("compatibility_status", ""),
                        created_at=datetime.datetime.utcnow()
                    )
                    db.session.add(build)
                    builds_added += 1
                db.session.commit()
            except Exception:
                db.session.rollback()
                continue

        logger.info(f"Database updated successfully! Components: {len(components)}, Links added: {added}, Unmatched links: {unmatched}, Users added: {users_added}, Builds added: {builds_added}")
        
        return {
            "components": len(components),
            "links_added": added,
            "unmatched_links": unmatched,
            "users_added": users_added,
            "builds_added": builds_added
        }


def register_cli_commands(app):
    """Register database update command with Flask CLI"""
    @app.cli.command()
    def update_db():
        """Update database with JSON data"""
        try:
            result = update_database()
            logger.info("Database update completed successfully")
            print(f"✓ Database updated: {result['components']} components, {result['links_added']} links, {result['users_added']} users")
        except Exception as e:
            logger.error(f"Database update failed: {str(e)}", exc_info=True)
            print(f"✗ Database update failed: {str(e)}")
            return 1
        return 0


if __name__ == "__main__":
    # Direct execution as a standalone script
    try:
        result = update_database()
        print(f"✓ Database updated successfully!")
        print(f"  Components: {result['components']}")
        print(f"  Links added: {result['links_added']}")
        print(f"  Unmatched links: {result['unmatched_links']}")
        print(f"  Users added: {result['users_added']}")
        print(f"  Builds added: {result['builds_added']}")
    except Exception as e:
        print(f"✗ Database update failed: {str(e)}")
        sys.exit(1)