from models.component import Component


class Motherboard:

    @staticmethod
    def get_all_motherboards():
        return Component.query.filter_by(category="Motherboard").all()

    @staticmethod
    def get_motherboard_by_name(name):
        return Component.query.filter_by(category="Motherboard", name=name).first()

    @staticmethod
    def get_motherboards_by_brand(brand):
        return Component.query.filter_by(category="Motherboard", brand=brand).all()

    @staticmethod
    def get_motherboards_by_socket_type(socket_type):
        motherboards = Motherboard.get_all_motherboards()
        result = []
        for mb in motherboards:
            if mb.specs.get("socket_type") == socket_type:
                result.append(mb)
        return result

    @staticmethod
    def get_motherboards_by_form_factor(form_factor):
        motherboards = Motherboard.get_all_motherboards()
        result = []
        for mb in motherboards:
            if mb.specs.get("form_factor") == form_factor:
                result.append(mb)
        return result

    @staticmethod
    def get_motherboards_by_ram_type(ram_type):
        motherboards = Motherboard.get_all_motherboards()
        result = []
        for mb in motherboards:
            if mb.specs.get("ram_type") == ram_type:
                result.append(mb)
        return result

    @staticmethod
    def get_motherboards_by_slots(slots):
        motherboards = Motherboard.get_all_motherboards()
        result = []
        for mb in motherboards:
            if mb.specs.get("slots") == slots:
                result.append(mb)
        return result

    @staticmethod
    def get_motherboards_by_max_ram(max_ram):
        motherboards = Motherboard.get_all_motherboards()
        result = []
        for mb in motherboards:
            if mb.specs.get("max_ram") == max_ram:
                result.append(mb)
        return result

    @staticmethod
    def get_motherboards_by_chipset(chipset):
        motherboards = Motherboard.get_all_motherboards()
        result = []
        for mb in motherboards:
            if mb.specs.get("chipset") == chipset:
                result.append(mb)
        return result

    @staticmethod
    def get_motherboards_by_m2_slots(m2_slots):
        motherboards = Motherboard.get_all_motherboards()
        result = []
        for mb in motherboards:
            if mb.specs.get("m2_slots") == m2_slots:
                result.append(mb)
        return result

    @staticmethod
    def get_motherboards_by_sata_ports(sata_ports):
        motherboards = Motherboard.get_all_motherboards()
        result = []
        for mb in motherboards:
            if mb.specs.get("sata_ports") == sata_ports:
                result.append(mb)
        return result

    @staticmethod
    def get_motherboard_socket_type(name):
        mb = Motherboard.get_motherboard_by_name(name)
        if mb:
            return mb.specs.get("socket_type")
        return None

    @staticmethod
    def get_motherboard_form_factor(name):
        mb = Motherboard.get_motherboard_by_name(name)
        if mb:
            return mb.specs.get("form_factor")
        return None

    @staticmethod
    def get_motherboard_ram_type(name):
        mb = Motherboard.get_motherboard_by_name(name)
        if mb:
            return mb.specs.get("ram_type")
        return None

    @staticmethod
    def get_motherboard_slots(name):
        mb = Motherboard.get_motherboard_by_name(name)
        if mb:
            return mb.specs.get("slots")
        return None

    @staticmethod
    def get_motherboard_max_ram(name):
        mb = Motherboard.get_motherboard_by_name(name)
        if mb:
            return mb.specs.get("max_ram")
        return None

    @staticmethod
    def get_motherboard_chipset(name):
        mb = Motherboard.get_motherboard_by_name(name)
        if mb:
            return mb.specs.get("chipset")
        return None

    @staticmethod
    def get_motherboard_m2_slots(name):
        mb = Motherboard.get_motherboard_by_name(name)
        if mb:
            return mb.specs.get("m2_slots")
        return None

    @staticmethod
    def get_motherboard_sata_ports(name):
        mb = Motherboard.get_motherboard_by_name(name)
        if mb:
            return mb.specs.get("sata_ports")
        return None
