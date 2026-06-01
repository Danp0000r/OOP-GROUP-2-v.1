from models.component import Component

class RAM:
    @staticmethod
    def get_all_ram():
        return Component.query.filter_by(
            category="RAM"
        ).all()

    @staticmethod
    def get_all_rams():
        return RAM.get_all_ram()

    @staticmethod
    def get_ram_by_name(name):
        return Component.query.filter_by(
            category="RAM",
            name=name
        ).first()

    @staticmethod
    def get_ram_name(name):
        return RAM.get_ram_by_name(name)

    @staticmethod
    def get_ram_brand(brand):

        return Component.query.filter_by(
            category="RAM",
            brand=brand
        ).all()

    @staticmethod
    def get_ram_by_type(ram_type):
        rams = RAM.get_all_ram()
        result = []
        for ram in rams:
            if ram.specs.get("type") == ram_type:
                result.append(ram)
        return result

    @staticmethod
    def get_ram_by_capacity(capacity):
        rams = RAM.get_all_ram()
        result = []
        for ram in rams:
            if ram.specs.get("capacity") == capacity:
                result.append(ram)
        return result

    @staticmethod
    def get_ram_by_speed(speed):
        rams = RAM.get_all_ram()
        result = []
        for ram in rams:
            if ram.specs.get("speed") == speed:
                result.append(ram)
        return result

    @staticmethod
    def get_ram_by_modules(modules):
        rams = RAM.get_all_ram()
        result = []
        for ram in rams:
            if ram.specs.get("modules") == modules:
                result.append(ram)
        return result

    @staticmethod
    def get_ram_by_latency(latency):
        rams = RAM.get_all_ram()
        result = []
        for ram in rams:
            if ram.specs.get("latency") == latency:
                result.append(ram)
        return result

    @staticmethod
    def get_ram_type(name):
        ram = RAM.get_ram_by_name(name)
        if ram:
            return ram.specs.get("type")
        return None

    @staticmethod
    def get_ram_capacity(name):
        ram = RAM.get_ram_by_name(name)
        if ram:
            return ram.specs.get("capacity")
        return None

    @staticmethod
    def get_ram_speed(name):
        ram = RAM.get_ram_by_name(name)
        if ram:
            return ram.specs.get("speed")
        return None

    @staticmethod
    def get_ram_modules(name):
        ram = RAM.get_ram_by_name(name)
        if ram:
            return ram.specs.get("modules")
        return None

    @staticmethod
    def get_ram_latency(name):
        ram = RAM.get_ram_by_name(name)
        if ram:
            return ram.specs.get("latency")
        return None
