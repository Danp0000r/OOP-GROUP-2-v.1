import json
from flask import Blueprint, render_template, redirect, url_for, flash, request, session, jsonify, Response
from database.db import db
from models.build import Build
from models.component import Component
from models.user import User
from services.compatibility.compatibility_service import CompatibilityService
from services.compare_builds_service import compare_builds


def parse_component_ids(value):
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value) if value else []
        except Exception:
            return []
    return []

build_bp = Blueprint("build", __name__)


@build_bp.route("/builder")
def builder():
    from sqlalchemy.orm import joinedload
    
    # Check if a build_id is provided to load
    build_id = request.args.get("build_id")
    selected_build = None
    
    if build_id:
        try:
            build_id = int(build_id)
            selected_build = Build.query.get(build_id)
            if selected_build and selected_build.user_id != session.get("user_id"):
                selected_build = None
        except (ValueError, TypeError):
            selected_build = None
    
    components = Component.query.options(joinedload(Component.links)).order_by(Component.category).all()
    categories = sorted(set(c.category for c in components))
    
    return render_template(
        "builder/builder.html",
        components=components,
        categories=categories,
        is_admin=session.get("is_admin", False),
        selected_build=selected_build,
        selected_build_components=parse_component_ids(selected_build.component_ids) if selected_build else []
    )


@build_bp.route("/builds")
def saved_builds():
    if "user_id" not in session:
        flash("Please log in to view your builds.", "warning")
        return redirect(url_for("auth.login"))
    user = User.query.get(session["user_id"])
    if not user:
        session.pop("user_id", None)
        session.pop("username", None)
        session.pop("is_admin", None)
        flash("Your session is no longer valid. Please log in again.", "warning")
        return redirect(url_for("auth.login"))

    builds = Build.query.filter_by(user_id=session["user_id"]).order_by(Build.created_at.desc()).all()

    total_spend = 0
    total_parts = 0
    for b in builds:
        ids = parse_component_ids(b.component_ids)
        total_parts += len(ids)
        comps = Component.query.filter(Component.component_id.in_(ids)).all()
        total_spend += sum(c.price for c in comps)

    avg_cost = total_spend / len(builds) if builds else 0

    return render_template(
        "builder/saved_builds.html",
        user=user,
        builds=builds,
        total_spend=total_spend,
        avg_cost=avg_cost,
        total_parts=total_parts,
    )


@build_bp.route("/api/builds/save", methods=["POST"])
def save_build():
    if "user_id" not in session:
        return jsonify({"error": "Login required"}), 401
    data          = request.get_json()
    name          = data.get("name", "My Build")
    component_ids = data.get("component_ids", [])
    build = Build(
        name=name,
        user_id=session["user_id"],
        component_ids=json.dumps(component_ids),
    )
    db.session.add(build)
    db.session.commit()
    return jsonify({"message": "Build saved!", "id": build.id})


@build_bp.route("/api/builds/<int:build_id>", methods=["DELETE"])
def delete_build(build_id):
    if "user_id" not in session:
        return jsonify({"error": "Login required"}), 401
    build = Build.query.filter_by(build_id=build_id, user_id=session["user_id"]).first()
    if not build:
        return jsonify({"error": "Build not found"}), 404
    db.session.delete(build)
    db.session.commit()
    return jsonify({"message": "Build deleted."})


@build_bp.route("/api/builds/<int:build_id>", methods=["PATCH"])
def update_build(build_id):
    if "user_id" not in session:
        return jsonify({"error": "Login required"}), 401
    build = Build.query.filter_by(build_id=build_id, user_id=session["user_id"]).first()
    if not build:
        return jsonify({"error": "Build not found"}), 404
    data = request.get_json() or {}
    
    # Update name if provided
    name = data.get("name")
    if name is not None:
        build.name = str(name).strip() or "My Build"
    
    # Update component_ids if provided
    component_ids = data.get("component_ids")
    if component_ids is not None:
        if isinstance(component_ids, list):
            build.component_ids = json.dumps(component_ids)
        else:
            return jsonify({"error": "component_ids must be a list"}), 400
    
    # Check if anything was updated
    if name is None and component_ids is None:
        return jsonify({"error": "No fields to update."}), 400
    
    db.session.commit()
    return jsonify({"message": "Build updated.", "name": build.name})


@build_bp.route("/api/builds/import", methods=["POST"])
def import_build():
    if "user_id" not in session:
        return jsonify({"error": "Login required"}), 401

    # Accept JSON body or file upload (JSON file) or plain text export
    data = None
    if request.is_json:
        data = request.get_json()
    elif 'file' in request.files:
        # uploaded file — try JSON first, otherwise treat as text
        raw = request.files['file'].read()
        try:
            data = json.loads(raw.decode('utf-8'))
        except Exception:
            try:
                data = raw.decode('utf-8')
            except Exception:
                return jsonify({"error": "Invalid file encoding."}), 400
    else:
        # raw body: could be JSON or plain text
        raw = request.get_data(as_text=True) or ''
        raw_stripped = raw.strip()
        if raw_stripped.startswith('{') or raw_stripped.startswith('['):
            try:
                data = json.loads(raw_stripped)
            except Exception:
                return jsonify({"error": "Invalid JSON body."}), 400
        else:
            data = raw

    # If it's a JSON import, expect name + component_ids
    if data and isinstance(data, dict) and 'component_ids' in data and isinstance(data['component_ids'], list):
        component_ids = [int(x) for x in data['component_ids'] if str(x).isdigit()]
        build = Build(
            name=data.get('name', 'Imported Build'),
            user_id=session['user_id'],
            component_ids=json.dumps(component_ids),
        )
        db.session.add(build)
        db.session.commit()
        return jsonify({"message": "Build imported.", "id": build.id, "name": build.name})

    # Otherwise, try to parse a plaintext export (.txt) created by export_build()
    # Expected lines: "<category> <name> (Brand)  —  P<price>". We'll extract name and brand and try to resolve components.
    if data and isinstance(data, str):
        text = data
    else:
        # if original request was a file, `data` may be None here; try raw body
        text = request.get_data(as_text=True) or ''

    if text:
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        # try to find component lines after header divider
        comp_lines = []
        for l in lines:
            # skip header/date/divider lines
            if l.startswith('BuildLab') or l.startswith('Saved:') or set(l) == {'='}:
                continue
            # match category + name + (brand) — categories and names separated by multiple spaces
            import re
            m = re.match(r"^(?P<category>.+?)\s{2,}(?P<name>.+?)\s*\((?P<brand>[^)]+)\)\s*[-–—]{1,3}\s*P(?P<price>[0-9,\,\.]+)$", l)
            if m:
                comp_lines.append((m.group('name').strip(), m.group('brand').strip()))
        # Resolve component ids by exact name+brand then name-only fallback
        resolved_ids = []
        from models.component import Component as CompModel
        for name, brand in comp_lines:
            c = CompModel.query.filter_by(name=name, brand=brand).first()
            if not c:
                # try case-insensitive name match
                c = CompModel.query.filter(CompModel.name.ilike(f"%{name}%"), CompModel.brand.ilike(f"%{brand}%")).first()
            if not c:
                c = CompModel.query.filter(CompModel.name.ilike(f"%{name}%")).first()
            if c:
                resolved_ids.append(c.component_id)

        if not resolved_ids:
            return jsonify({"error": "Could not resolve any components from the provided text. Try JSON import or ensure names/brands match."}), 400

        build = Build(
            name=(lines[0] if lines else 'Imported Build'),
            user_id=session['user_id'],
            component_ids=json.dumps(resolved_ids),
        )
    db.session.add(build)
    db.session.commit()
    return jsonify({"message": "Build imported.", "id": build.id, "name": build.name})


@build_bp.route("/builds/<int:build_id>/export")
def export_build(build_id):
    if "user_id" not in session:
        flash("Please log in to export builds.", "warning")
        return redirect(url_for("auth.login"))
    build = Build.query.filter_by(build_id=build_id, user_id=session["user_id"]).first()
    if not build:
        flash("Build not found.", "danger")
        return redirect(url_for("build.saved_builds"))

    component_ids = parse_component_ids(build.component_ids)
    components    = Component.query.filter(Component.component_id.in_(component_ids)).all()
    comp_map      = {c.id: c for c in components}

    lines = []
    lines.append(f"BuildLab — {build.name}")
    lines.append(f"Saved: {build.created_at.strftime('%B %d, %Y')}")
    lines.append("=" * 40)

    total = 0
    for cid in component_ids:
        c = comp_map.get(cid)
        if c:
            lines.append(f"{c.category:<14} {c.name} ({c.brand})  —  P{c.price:,.0f}")
            total += c.price

    lines.append("=" * 40)
    lines.append(f"{'TOTAL':<14} P{total:,.0f}")

    content  = "\n".join(lines)
    filename = build.name.replace(" ", "_") + ".txt"
    return Response(
        content,
        mimetype="text/plain",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@build_bp.route("/api/compatibility", methods=["POST"])
def compatibility():
    data          = request.get_json()
    component_ids = data.get("component_ids", [])
    components    = Component.query.filter(Component.component_id.in_(component_ids)).all()
    # CompatibilityService can accept a list of component dicts (with prices)
    comp_list = []
    for c in components:
        comp_list.append({
            "name": c.name,
            "category": c.category,
            "brand": c.brand,
            "specs": c.specs or {},
            "price": c.price,
        })
    result = CompatibilityService.evaluate_build(comp_list)
    return jsonify(result)


@build_bp.route("/api/compatibility/evaluate", methods=["POST"])
def compatibility_evaluate():
    """Evaluate a free-form parts string and return full compatibility report.

    Expects JSON: { "parts": "Intel i5-12400F, RTX 4060, 750W 80+ Gold PSU" }
    """
    data = request.get_json(silent=True) or {}
    parts = data.get('parts') or data.get('query') or ''
    if not parts:
        return jsonify({"error": "No parts provided."}), 400
    # CompatibilityService accepts a string or list; pass through the raw string
    result = CompatibilityService.evaluate_build(parts)
    return jsonify(result)


@build_bp.route("/api/builds/<int:build_id>/load")
def load_build(build_id):
    if "user_id" not in session:
        return jsonify({"error": "Login required"}), 401
    build = Build.query.filter_by(build_id=build_id, user_id=session["user_id"]).first()
    if not build:
        return jsonify({"error": "Build not found"}), 404
    component_ids = parse_component_ids(build.component_ids)
    components = Component.query.filter(Component.component_id.in_(component_ids)).all()
    comp_data = [{"id": c.id, "name": c.name, "brand": c.brand, "category": c.category, "price": c.price} for c in components]
    return jsonify({"name": build.name, "components": comp_data})


@build_bp.route("/api/builds/user")
def user_builds():
    if "user_id" not in session:
        return jsonify({"error": "Login required"}), 401
    builds = Build.query.filter_by(user_id=session["user_id"]).order_by(Build.created_at.desc()).all()
    result = []
    for b in builds:
        ids = parse_component_ids(b.component_ids)
        comps = Component.query.filter(Component.component_id.in_(ids)).all()
        total = sum(c.price for c in comps)
        result.append({
            "id": b.id,
            "name": b.name,
            "created_at": b.created_at.strftime('%b %d, %Y'),
            "part_count": len(ids),
            "total": total,
            "component_ids": ids,
        })
    return jsonify(result)


@build_bp.route("/api/builds/compare")
def compare_builds_route():
    if "user_id" not in session:
        return jsonify({"error": "Login required"}), 401

    raw_ids = request.args.get('ids', '')
    if not raw_ids:
        return jsonify({"error": "No builds selected."}), 400

    build_ids = []
    for raw_id in raw_ids.split(','):
        raw_id = raw_id.strip()
        if raw_id.isdigit():
            build_ids.append(int(raw_id))

    if not build_ids:
        return jsonify({"error": "No valid build IDs provided."}), 400

    payload = compare_builds(build_ids, session['user_id'])
    if not payload.get('items'):
        return jsonify({"error": "No matching builds found."}), 404

    return jsonify(payload)


@build_bp.route("/builds/share/<int:build_id>")
def share_build_page(build_id):
    build = Build.query.get_or_404(build_id)
    component_ids = parse_component_ids(build.component_ids)
    components = Component.query.filter(Component.component_id.in_(component_ids)).all()
    total = sum(c.price for c in components)
    return render_template("builder/share_preview.html", build=build, components=components, total=total)
