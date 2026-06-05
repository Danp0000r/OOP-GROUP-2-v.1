from models.component import Component


class Case:

    @staticmethod
    def get_all_cases():
        return Component.query.filter_by(category="Case").all()

    @staticmethod
    def get_case_by_name(name):
        return Component.query.filter_by(category="Case", name=name).first()

    @staticmethod
    def get_cases_by_brand(brand):
        return Component.query.filter_by(category="Case", brand=brand).all()

    @staticmethod
    def get_cases_by_form_factor(form_factor):
        cases = Case.get_all_cases()
        result = []
        for case in cases:
            if case.specs.get("form_factor") == form_factor:
                result.append(case)
        return result

    @staticmethod
    def get_cases_by_gpu_length_limit(limit):
        cases = Case.get_all_cases()
        result = []
        for case in cases:
            if case.specs.get("gpu_length_limit") == limit:
                result.append(case)
        return result

    @staticmethod
    def get_cases_by_cpu_cooler_height_limit(limit):
        cases = Case.get_all_cases()
        result = []
        for case in cases:
            if case.specs.get("cpu_cooler_limit_mm") == limit:
                result.append(case)
        return result

    @staticmethod
    def get_cases_by_included_fans(fans):
        cases = Case.get_all_cases()
        result = []
        for case in cases:
            if case.specs.get("included_fans") == fans:
                result.append(case)
        return result

    @staticmethod
    def get_case_form_factor(name):
        case = Case.get_case_by_name(name)
        if case:
            return case.specs.get("form_factor")
        return None

    @staticmethod
    def get_case_gpu_length_limit(name):
        case = Case.get_case_by_name(name)
        if case:
            return case.specs.get("gpu_length_limit")
        return None

    @staticmethod
    def get_case_cpu_cooler_height_limit(name):
        case = Case.get_case_by_name(name)
        if case:
            return case.specs.get("cpu_cooler_limit_mm")
        return None

    @staticmethod
    def get_case_included_fans(name):
        case = Case.get_case_by_name(name)
        if case:
            return case.specs.get("included_fans")
        return None
