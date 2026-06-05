import re

class Utils:

    @staticmethod
    def norm(text):
        if not text:
            return ""
        return " ".join(re.findall(r"[a-z0-9]+", re.sub(r"[_\-]+", " ", str(text)).lower()))

    @staticmethod
    def num(value):
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        d = re.findall(r"\d+\.?\d*", str(value))
        return float(d[0]) if d else None

    @staticmethod
    def split(parts_input):
        if isinstance(parts_input, str):
            return [p.strip() for p in re.split(r"[,;\n]+", parts_input) if p.strip()]
        return [str(p).strip() for p in parts_input if str(p).strip()]