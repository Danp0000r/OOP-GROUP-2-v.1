from services.compatibility.component_loader import ComponentLoader
from services.compatibility.utils import Utils


class ComponentMatcher:
    """Fuzzy-matches user input to known components."""

    @staticmethod
    def get_component(name):
        """
        Find the best-matching component for a given name string.
        Returns the component dict or None.
        
        Strategy:
        1. Exact name/ID match
        2. Contains match (prefer longest exact match to avoid weaker matches)
        3. Token-based fuzzy match (≥95% threshold)
        """
        if not name:
            return None

        components = ComponentLoader.load()
        query = Utils.norm(name)
        query_tokens = query.split()

        # 1) Exact match on name or id
        for c in components:
            if Utils.norm(c.get("name", "")) == query:
                return c
            if Utils.norm(c.get("id", "")) == query:
                return c

        # 2) Contains match - prefer the shortest valid close match
        #    so base SKUs like "RTX 4060" win over longer variants.
        contains_matches = []
        for c in components:
            if query in Utils.norm(c.get("name", "")):
                contains_matches.append(c)
        
        if contains_matches:
            # Return the shortest matching name to prefer exact/base SKUs.
            return min(contains_matches, key=lambda x: len(Utils.norm(x.get("name", ""))))

        # 3) Token-based match (≥95% threshold)
        best_score, best = 0, None
        for c in components:
            search = Utils.norm(c.get("name", "")) + " " + Utils.norm(c.get("brand", ""))
            tokens = set(search.split())
            matched = sum(1 for t in query_tokens if t in tokens)
            score = matched / max(len(query_tokens), 1)
            if score > best_score:
                best_score, best = score, c

        return best if best_score >= 0.95 else None

    @staticmethod
    def detect_components(parts_input):
        """
        Split user input and try to identify every part.
        Returns a list of detection results.
        
        Note: Unknown parts don't block analysis - known components are checked,
        unknown ones are marked for manual verification.
        """
        parts = Utils.split(parts_input)
        results = []
        for part in parts:
            comp = ComponentMatcher.get_component(part)
            if comp:
                results.append({
                    "input": part,
                    "component": comp,
                    "source": "database",
                    "verified": True
                })
            else:
                results.append({
                    "input": part,
                    "component": None,
                    "source": "unknown",
                    "verified": False,
                    "note": f"'{part}' not found in database. Add manually or verify compatibility separately."
                })
        return results