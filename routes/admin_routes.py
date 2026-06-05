
import json
import os
import re
from urllib.parse import urlparse, urlunparse
from flask import Blueprint, render_template, redirect, url_for, request, flash, session, jsonify
from functools import wraps
from sqlalchemy.exc import IntegrityError
from database.db import db
from models.component import Component
from models.link      import Link
from models.user      import User
from models.build     import Build
from services.cache import clear_cache

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("user_id") or not session.get("is_admin"):
            flash("Admin access required.", "danger")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated


@admin_bp.route("/")
@admin_required
def dashboard():
    from sqlalchemy import func
    import datetime
    
    cat_counts = dict(db.session.query(Component.category, func.count(Component.component_id)).group_by(Component.category).all())
    stats = {
        "components":  Component.query.count(),
        "users":       User.query.count(),
        "builds":      Build.query.count(),
        "links":       Link.query.count(),
        "by_category": cat_counts,
    }
    components = Component.query.order_by(Component.category, Component.name).all()
    users = User.query.order_by(User.created_at.desc()).all()
    
    # Add online status to each user (based on last_active timestamp)
    inactivity_timeout_seconds = 120
    now = datetime.datetime.utcnow()
    for user in users:
        if user.last_active:
            time_since_last_active = (now - user.last_active).total_seconds()
            user.is_online = time_since_last_active < inactivity_timeout_seconds
        else:
            user.is_online = False
    
    return render_template("admin/dashboard.html", stats=stats, components=components, users=users)


@admin_bp.route("/components")
@admin_required
def manage_components():
    category = request.args.get("category", "")
    search   = request.args.get("search", "")
    q = Component.query
    if category:
        q = q.filter_by(category=category)
    if search:
        q = q.filter(Component.name.ilike(f"%{search}%"))
    components = q.order_by(Component.category, Component.name).all()
    selected_id = request.args.get("selected")
    categories = db.session.query(Component.category).distinct().all()
    return render_template("admin/manage_components.html",
                           components=components,
                           categories=[c[0] for c in categories],
                           search=search, active_category=category,
                           selected_component_id=selected_id)


def parse_json_field(value, default=None):
    if default is None:
        default = {}
    if isinstance(value, dict):
        return value
    if value is None:
        return default
    value = value.strip()
    if not value:
        return default
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, dict) else default
    except (ValueError, TypeError):
        return default


def normalize_external_id(value, name):
    raw = (value or "").strip()
    if raw:
        return raw
    slug = re.sub(r"[^a-z0-9]+", "_", name.strip().lower())
    slug = slug.strip("_")
    if slug:
        return slug
    return f"component_{os.urandom(4).hex()}"


def _normalize_pending_links(raw_links):
    normalized = []
    seen = set()
    for item in raw_links or []:
        store = (item.get('store_name') or item.get('store') or '').strip()
        url = (item.get('url') or '').strip()
        if not url:
            continue
        if url and not re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*://', url):
            url = f'https://{url}'
        try:
            price = float(item.get('price', 0) or 0)
        except (ValueError, TypeError):
            continue
        if price <= 0:
            continue
        key = (store.lower(), url.lower(), price)
        if key in seen:
            continue
        seen.add(key)
        normalized.append({'store_name': store, 'url': url, 'price': price})
    return normalized


def _redirect_back(default_endpoint="admin.manage_components"):
    referrer = request.referrer
    if not referrer:
        return redirect(url_for(default_endpoint))

    parsed = urlparse(referrer)
    if parsed.scheme not in ("http", "https") or parsed.netloc != request.host:
        return redirect(url_for(default_endpoint))

    path = parsed.path or "/"
    if path.rstrip("/") == "/admin":
        return redirect(url_for("admin.dashboard", tab="components"))

    return redirect(urlunparse(("", "", path, parsed.params, parsed.query, parsed.fragment)))


@admin_bp.route("/components/add", methods=["POST"])
@admin_required
def add_component():
    price_val = 0
    try:
        price_val = float(request.form.get("price", 0) or 0)
    except ValueError:
        price_val = 0
    try:
        perf_score = int(request.form.get("performance_score", 50) or 50)
    except ValueError:
        perf_score = 50

    specs_data = parse_json_field(request.form.get("specs", ""))
    compatibility_data = parse_json_field(request.form.get("compatibility", ""))
    extra_data = parse_json_field(request.form.get("extra", ""))
    geometry_data = parse_json_field(request.form.get("geometry", ""))
    if isinstance(extra_data, dict):
        specs_data.update(extra_data)
    if isinstance(geometry_data, dict) and geometry_data:
        specs_data["geometry"] = geometry_data

    pending_links = []
    pending_prices = []
    pending_raw = request.form.get('pending_links', '')
    if pending_raw:
        try:
            parsed_pending = json.loads(pending_raw)
            if isinstance(parsed_pending, list):
                pending_links = _normalize_pending_links(parsed_pending)
        except Exception:
            pending_links = []
    for item in (pending_links or []):
        try:
            item_price = float(item.get('price', 0) or 0)
        except (ValueError, TypeError):
            continue
        if item_price > 0:
            pending_prices.append(item_price)
    if pending_prices:
        price_val = min(pending_prices)

    external_id = normalize_external_id(request.form.get("external_id", ""), request.form.get("name", ""))

    existing_component = Component.query.filter_by(external_id=external_id).first()
    if existing_component:
        flash(f"External ID '{external_id}' is already in use. Please choose a different external ID.", "danger")
        return redirect(url_for("admin.manage_components"))

    c = Component(
        external_id=external_id,
        name=request.form["name"],
        brand=request.form["brand"],
        category=request.form["category"],
        price=price_val,
        specs=specs_data,
        compatibility=compatibility_data,
        performance_score=perf_score,
        image_url=request.form.get("image_url", "") or "",
        description=request.form.get("description", "") or ""
    )
    db.session.add(c)
    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        flash("Failed to add component: duplicate external ID or database constraint violation.", "danger")
        return redirect(url_for("admin.manage_components"))

    # handle any pending links submitted along with the new component
    for p in (pending_links or []):
        raw_url = (p.get('url', '') or '').strip()
        if raw_url and not re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*://', raw_url):
            raw_url = f'https://{raw_url}'
        link = Link(component_id=c.component_id, store=p.get('store_name') or p.get('store') or '', url=raw_url, price=float(p.get('price') or 0))
        db.session.add(link)
    if pending_links:
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash("Component was added but links could not be saved. Please edit the component to add links.", "warning")
            return redirect(url_for("admin.manage_components"))

    clear_cache()
    flash(f"Component '{c.name}' added.", "success")
    return _redirect_back()


@admin_bp.route("/components/edit/<int:cid>", methods=["POST"])
@admin_required
def edit_component(cid):
    c = Component.query.get_or_404(cid)
    c.name = request.form["name"]
    c.brand = request.form["brand"]
    c.category = request.form["category"]
    c.external_id = normalize_external_id(request.form.get("external_id", ""), c.name)
    price_val = request.form.get("price")
    if price_val is not None and price_val.strip() != "":
        try:
            c.price = float(price_val)
        except ValueError:
            c.price = 0
    try:
        c.performance_score = int(request.form.get("performance_score", 50) or 50)
    except ValueError:
        c.performance_score = 50
    c.specs = parse_json_field(request.form.get("specs", ""))
    extra_data = parse_json_field(request.form.get("extra", ""))
    geometry_data = parse_json_field(request.form.get("geometry", ""))
    if isinstance(extra_data, dict):
        c.specs.update(extra_data)
    if isinstance(geometry_data, dict) and geometry_data:
        specs = c.specs or {}
        specs["geometry"] = geometry_data
        c.specs = specs
    c.compatibility = parse_json_field(request.form.get("compatibility", ""))
    c.image_url = request.form.get("image_url", "") or ""
    c.description = request.form.get("description", "") or ""

    pending_links = []
    raw_pending = request.form.get("pending_links", "[]")
    try:
        parsed_pending = json.loads(raw_pending) if raw_pending else []
        if isinstance(parsed_pending, list):
            pending_links = _normalize_pending_links(parsed_pending)
    except Exception:
        pending_links = []

    db.session.commit()

    if pending_links:
        db.session.query(Link).filter_by(component_id=c.component_id).delete()
        for p in pending_links:
            raw_url = (p.get("url", "") or "").strip()
            if raw_url and not re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*://', raw_url):
                raw_url = f'https://{raw_url}'
            link = Link(component_id=c.component_id, store=p.get('store_name') or p.get('store') or '', url=raw_url, price=float(p.get('price') or 0))
            db.session.add(link)
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash("Component updated, but links could not be saved.", "warning")
            return _redirect_back()

    from sqlalchemy import func
    min_price = db.session.query(func.min(Link.price)).filter_by(component_id=c.component_id).scalar()
    if min_price is not None:
        c.price = float(min_price)
        db.session.commit()

    clear_cache()
    flash(f"Component '{c.name}' updated.", "success")
    return _redirect_back()


@admin_bp.route("/components/delete/<int:cid>", methods=["POST"])
@admin_required
def delete_component(cid):
    c = Component.query.get_or_404(cid)
    db.session.delete(c)
    db.session.commit()
    clear_cache()
    flash(f"Deleted '{c.name}'.", "warning")
    return _redirect_back()


@admin_bp.route("/components/<int:cid>/links")
@admin_required
def get_links(cid):
    links = Link.query.filter_by(component_id=cid).all()
    return jsonify({"links": [l.to_dict() for l in links]})


@admin_bp.route("/components/<int:cid>/details")
@admin_required
def get_component_details(cid):
    c = Component.query.get_or_404(cid)
    return jsonify({
        "id": c.id,
        "name": c.name,
        "brand": c.brand,
        "category": c.category,
        "external_id": c.external_id,
        "price": c.price,
        "performance_score": c.performance_score,
        "image_url": c.image_url,
        "description": c.description,
        "specs": c.specs or {},
        "compatibility": c.compatibility or {},
        "links": [
            {"id": l.link_id, "store": l.store, "url": l.url, "price": l.price}
            for l in c.links
        ]
    })


@admin_bp.route("/components/<int:cid>/links/add", methods=["POST"])
@admin_required
def add_link(cid):
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({"error": "Invalid data"}), 400
    raw_url = (data.get("url", "") or "").strip()
    if raw_url and not re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*://', raw_url):
        raw_url = f"https://{raw_url}"

    link = Link(
        component_id=cid,
        store=data.get("store_name", ""),
        url=raw_url,
        verified=bool(data.get("verified", False)),
    )
    db.session.add(link)
    db.session.commit()
    clear_cache()
    return jsonify({"message": "Link added.", "link": link.to_dict()})


@admin_bp.route("/links/<int:lid>/delete", methods=["POST"])
@admin_required
def delete_link(lid):
    link = Link.query.get_or_404(lid)
    db.session.delete(link)
    db.session.commit()
    clear_cache()
    return jsonify({"message": "Link deleted."})


@admin_bp.route("/users/<int:uid>/delete", methods=["POST"])
@admin_required
def delete_user(uid):
    if uid == session.get("user_id"):
        return jsonify({"error": "Cannot delete your own account."}), 400
    user = User.query.get_or_404(uid)
    # Delete user's builds too
    Build.query.filter_by(user_id=uid).delete()
    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": f"User '{user.username}' deleted."})


@admin_bp.route("/users/<int:uid>/toggle-admin", methods=["POST"])
@admin_required
def toggle_admin(uid):
    if uid == session.get("user_id"):
        return jsonify({"error": "Cannot change your own admin status."}), 400
    user = User.query.get_or_404(uid)
    user.is_admin = not user.is_admin
    db.session.commit()
    return jsonify({"message": "Updated.", "is_admin": user.is_admin})


@admin_bp.route("/api/users/status", methods=["GET"])
@admin_required
def get_users_status():
    """Get online/offline status for all users (JSON endpoint for real-time updates)"""
    import datetime
    
    users = User.query.order_by(User.created_at.desc()).all()
    inactivity_timeout_seconds = 120  # Mark offline after 2 minutes of no heartbeat
    now = datetime.datetime.utcnow()
    
    users_data = []
    for user in users:
        # Determine if user is online
        is_online = False
        if user.last_active:
            time_since_last_active = (now - user.last_active).total_seconds()
            is_online = time_since_last_active < inactivity_timeout_seconds
        
        users_data.append({
            'id': user.user_id,
            'username': user.username,
            'email': user.email,
            'is_admin': user.is_admin,
            'is_online': is_online,
            'last_active': user.last_active.isoformat() if user.last_active else None,
            'profile_picture': user.profile_picture
        })
    
    return jsonify({
        "success": True,
        "users": users_data,
        "timestamp": now.isoformat()
    })
