from models.component import Component
from models.link import Link


def calculate_build_total(component_ids: list) -> dict:
    components = Component.query.filter(Component.component_id.in_(component_ids)).all()
    breakdown = [
        {"id": c.id, "name": c.name, "category": c.category, "price": c.price}
        for c in components
    ]
    total = sum(c["price"] for c in breakdown)
    return {"total": total, "breakdown": breakdown, "count": len(breakdown)}


def get_store_prices(component_id: int) -> dict:
    links = Link.query.filter_by(component_id=component_id).order_by(Link.price).all()
    if not links:
        return {"cheapest": None, "stores": []}
    stores = [{"store": l.store_name, "price": l.price, "url": l.url} for l in links]
    return {"cheapest": stores[0], "stores": stores}


def cheapest_build(component_ids: list) -> dict:
    breakdown, total = [], 0
    for cid in component_ids:
        result = get_store_prices(cid)
        comp = Component.query.get(cid)
        if comp and result["cheapest"]:
            entry = {
                "id": cid,
                "name": comp.name,
                "store": result["cheapest"]["store"],
                "price": result["cheapest"]["price"],
                "url": result["cheapest"]["url"],
            }
        elif comp:
            entry = {
                "id": cid,
                "name": comp.name,
                "store": "Base",
                "price": comp.price,
                "url": None,
            }
        else:
            continue
        breakdown.append(entry)
        total += entry["price"]
    return {"total": total, "breakdown": breakdown}


def price_budget_check(component_ids: list, budget: int) -> dict:
    result = calculate_build_total(component_ids)
    total = result["total"]
    over = total > budget
    diff = abs(total - budget)
    sorted_bd = sorted(result["breakdown"], key=lambda x: x["price"], reverse=True)
    return {
        "within_budget": not over,
        "total": total,
        "budget": budget,
        "difference": diff,
        "message": f"Over budget by ₱{diff:,}" if over else f"₱{diff:,} under budget",
        "savings_targets": sorted_bd[:3] if over else [],
    }
