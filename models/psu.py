from models.component import Component


class PSU:

    @staticmethod
    def get_all_psus():
        return Component.query.filter_by(category="PSU").all()

    @staticmethod
    def get_psu_by_name(name):
        return Component.query.filter_by(category="PSU", name=name).first()

    @staticmethod
    def get_psus_by_brand(brand):
        return Component.query.filter_by(category="PSU", brand=brand).all()

    @staticmethod
    def get_psus_by_wattage(wattage):
        psus = PSU.get_all_psus()
        result = []
        for psu in psus:
            if psu.specs.get("wattage") == wattage:
                result.append(psu)
        return result

    @staticmethod
    def get_psus_by_efficiency(efficiency):
        psus = PSU.get_all_psus()
        result = []
        for psu in psus:
            if psu.specs.get("efficiency") == efficiency:
                result.append(psu)
        return result

    @staticmethod
    def get_psus_by_modular(modular):
        psus = PSU.get_all_psus()
        result = []
        for psu in psus:
            if psu.specs.get("modular") == modular:
                result.append(psu)
        return result

    @staticmethod
    def get_psus_by_form_factor(form_factor):
        psus = PSU.get_all_psus()
        result = []
        for psu in psus:
            if psu.specs.get("form_factor") == form_factor:
                result.append(psu)
        return result

    @staticmethod
    def get_psu_wattage(name):
        psu = PSU.get_psu_by_name(name)
        if psu:
            return psu.specs.get("wattage")
        return None

    @staticmethod
    def get_psu_efficiency(name):
        psu = PSU.get_psu_by_name(name)
        if psu:
            return psu.specs.get("efficiency")
        return None

    @staticmethod
    def get_psu_modular(name):
        psu = PSU.get_psu_by_name(name)
        if psu:
            return psu.specs.get("modular")
        return None

    @staticmethod
    def get_psu_form_factor(name):
        psu = PSU.get_psu_by_name(name)
        if psu:
            return psu.specs.get("form_factor")
        return None
