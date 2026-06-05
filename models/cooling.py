from models.component import Component


class Cooling:

    @staticmethod
    def get_all_coolers():
        return Component.query.filter_by(category="Cooling").all()

    @staticmethod
    def get_all_cooling():
        return Cooling.get_all_coolers()

    @staticmethod
    def get_cooler_by_name(name):
        return Component.query.filter_by(category="Cooling", name=name).first()

    @staticmethod
    def get_coolers_by_brand(brand):
        return Component.query.filter_by(category="Cooling", brand=brand).all()

    @staticmethod
    def get_coolers_by_type(cooler_type):
        coolers = Cooling.get_all_coolers()
        result = []
        for cooler in coolers:
            if cooler.specs.get("type") == cooler_type:
                result.append(cooler)
        return result

    @staticmethod
    def get_coolers_by_size(size):
        coolers = Cooling.get_all_coolers()
        result = []
        for cooler in coolers:
            if cooler.specs.get("height_mm") == size:
                result.append(cooler)
        return result

    @staticmethod
    def get_coolers_by_tdp_rating(tdp_rating):
        coolers = Cooling.get_all_coolers()
        result = []
        for cooler in coolers:
            if cooler.specs.get("tdp_rating") == tdp_rating:
                result.append(cooler)
        return result

    @staticmethod
    def get_cooler_type(name):
        cooler = Cooling.get_cooler_by_name(name)
        if cooler:
            return cooler.specs.get("type")
        return None

    @staticmethod
    def get_cooler_size(name):
        cooler = Cooling.get_cooler_by_name(name)
        if cooler:
            return cooler.specs.get("height_mm")
        return None

    @staticmethod
    def get_cooler_tdp_rating(name):
        cooler = Cooling.get_cooler_by_name(name)
        if cooler:
            return cooler.specs.get("tdp_rating")
        return None
