from services.cache import memoize
from models.component import Component


@memoize(timeout=300)
def compare_components(component_ids: list) -> dict:
    """Build a compare payload for the selected component IDs."""
    components = Component.query.filter(Component.component_id.in_(component_ids)).all()
    component_map = {component.component_id: component for component in components}

    items = []
    for component_id in component_ids:
        component = component_map.get(component_id)
        if not component:
            continue
        item = component.to_dict()
        item["cat"] = item["category"]
        items.append(item)

    all_keys = sorted({
        key
        for item in items
        for key in (item.get("specs") or {}).keys()
    })

    same_type = len(items) > 0 and all(item["category"] == items[0]["category"] for item in items)

    export_lines = ["Component Comparison", "====================="]
    export_lines.extend(
        f"{item['category']} {index + 1}: {item['name']} ({item['brand']}) - ₱{item['price']:,}"
        for index, item in enumerate(items)
    )
    export_lines.append("")
    export_lines.append("Specs:")
    for key in all_keys:
        values = [
            (item.get("specs") or {}).get(key, "—")
            for item in items
        ]
        export_lines.append(f"{key}: {' | '.join(str(value) for value in values)}")

    return {
        "items": items,
        "all_keys": all_keys,
        "same_type": same_type,
        "export_text": "\n".join(export_lines)
    }
