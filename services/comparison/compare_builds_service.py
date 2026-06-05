import json
from models.build import Build
from models.component import Component
from services.compatibility.compatibility_service import CompatibilityService


def parse_component_ids(value):
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value) if value else []
        except Exception:
            return []
    return []


def compare_builds(build_ids: list, user_id: int) -> dict:
    builds = Build.query.filter(Build.id.in_(build_ids), Build.user_id == user_id).all()
    build_map = {build.id: build for build in builds}

    items = []
    for build_id in build_ids:
        build = build_map.get(build_id)
        if not build:
            continue

        component_ids = parse_component_ids(build.component_ids)
        components = Component.query.filter(Component.component_id.in_(component_ids)).all() if component_ids else []
        components = sorted(components, key=lambda c: (c.category or '', c.name or ''))

        total_price = sum(c.price for c in components)
        component_rows = [
            {
                "id": component.component_id,
                "name": component.name,
                "brand": component.brand,
                "category": component.category,
                "price": component.price,
            }
            for component in components
        ]

        items.append({
            "id": build.id,
            "name": build.name,
            "created_at": build.created_at.strftime('%b %d, %Y'),
            "part_count": len(component_ids),
            "total_price": total_price,
            "compatibility_status": build.compatibility_status or "Unknown",
            "components": component_rows,
            "compatibility_report": CompatibilityService.evaluate_build([
                {"name": c.name, "brand": c.brand, "category": c.category, "specs": c.specs or {}, "price": c.price, "performance_score": c.performance_score}
                for c in components
            ]) if components else {},
        })

    return {
        "items": items,
    }
