from flask import Blueprint, render_template, request, jsonify
from models.component import Component
from models.link import Link
from services.compare_parts_service import compare_components

component_bp = Blueprint("components", __name__)


@component_bp.route("/parts")
def parts():
    category = request.args.get("category", "")
    search   = request.args.get("search", "")
    min_price = request.args.get("min_price", type=float)
    max_price = request.args.get("max_price", type=float)

    query = Component.query
    if category:
        query = query.filter_by(category=category)
    if search:
        query = query.filter(
            (Component.name.ilike(f"%{search}%")) |
            (Component.brand.ilike(f"%{search}%"))
        )
    if min_price is not None:
        query = query.filter(Component.price >= min_price)
    if max_price is not None:
        query = query.filter(Component.price <= max_price)

    components = []
    for component in query.order_by(Component.category, Component.price).all():
        component_data = component.to_dict()
        component_data["specs"] = component_data.get("description", "")
        components.append(component_data)

    categories = sorted(set(c.category for c in Component.query.all()))
    return render_template("parts.html", components=components, categories=categories,
                           active_category=category, search=search)


@component_bp.route("/api/components")
def api_components():
    category  = request.args.get("category", "")
    search    = request.args.get("search", "")
    query = Component.query
    if category:
        query = query.filter_by(category=category)
    if search:
        query = query.filter(Component.name.ilike(f"%{search}%"))
    return jsonify([c.to_dict() for c in query.all()])


@component_bp.route("/api/components/<int:component_id>")
def api_component(component_id):
    component = Component.query.get_or_404(component_id)
    return jsonify(component.to_dict())


@component_bp.route("/api/components/<int:component_id>/links")
def component_links(component_id):
    links = Link.query.filter_by(component_id=component_id).all()
    return jsonify([l.to_dict() for l in links])


@component_bp.route("/api/components/compare")
def api_compare_components():
    ids = request.args.get("ids", "")
    if not ids:
        return jsonify({"error": "No component IDs provided."}), 400

    try:
        component_ids = [int(value.strip()) for value in ids.split(",") if value.strip()]
    except ValueError:
        return jsonify({"error": "Invalid component IDs."}), 400

    if not component_ids:
        return jsonify({"error": "No valid component IDs provided."}), 400

    result = compare_components(component_ids)
    if not result["items"]:
        return jsonify({"error": "No matching components found."}), 404

    return jsonify(result)
