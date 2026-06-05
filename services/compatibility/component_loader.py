from services.cache import memoize


class ComponentLoader:

    @staticmethod
    @memoize(timeout=600)
    def load():
        try:
            from models.component import Component
            components = Component.query.all()
            normalized = []
            for c in components:
                normalized.append({
                    "id": str(c.component_id),
                    "name": c.name,
                    "category": c.category,
                    "brand": c.brand,
                    "specs": c.specs or {},
                    "compatibility": c.compatibility or {},
                    "price": float(c.price or 0),
                    "performance_score": int(c.performance_score or 50)
                })
            return normalized
        except Exception as e:
            print(f"Error loading components from database: {e}")
            return []