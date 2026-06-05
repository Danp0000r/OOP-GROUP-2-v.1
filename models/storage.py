from models.component import Component


class Storage:

    @staticmethod
    def get_all_storage():
        return Component.query.filter_by(category="Storage").all()

    @staticmethod
    def get_storage_by_name(name):
        return Component.query.filter_by(category="Storage", name=name).first()

    @staticmethod
    def get_storage_by_brand(brand):
        return Component.query.filter_by(category="Storage", brand=brand).all()

    @staticmethod
    def get_storage_by_type(storage_type):
        drives = Storage.get_all_storage()
        result = []
        for drive in drives:
            if drive.specs.get("type") == storage_type:
                result.append(drive)
        return result

    @staticmethod
    def get_storage_by_capacity(capacity):
        drives = Storage.get_all_storage()
        result = []
        for drive in drives:
            if drive.specs.get("capacity") == capacity:
                result.append(drive)
        return result

    @staticmethod
    def get_storage_by_interface(interface):
        drives = Storage.get_all_storage()
        result = []
        for drive in drives:
            if drive.specs.get("interface") == interface:
                result.append(drive)
        return result

    @staticmethod
    def get_storage_by_read_speed(read_speed):
        drives = Storage.get_all_storage()
        result = []
        for drive in drives:
            if drive.specs.get("read_speed") == read_speed:
                result.append(drive)
        return result

    @staticmethod
    def get_storage_by_write_speed(write_speed):
        drives = Storage.get_all_storage()
        result = []
        for drive in drives:
            if drive.specs.get("write_speed") == write_speed:
                result.append(drive)
        return result

    @staticmethod
    def get_storage_type(name):
        drive = Storage.get_storage_by_name(name)
        if drive:
            return drive.specs.get("type")
        return None

    @staticmethod
    def get_storage_capacity(name):
        drive = Storage.get_storage_by_name(name)
        if drive:
            return drive.specs.get("capacity")
        return None

    @staticmethod
    def get_storage_interface(name):
        drive = Storage.get_storage_by_name(name)
        if drive:
            return drive.specs.get("interface")
        return None

    @staticmethod
    def get_storage_read_speed(name):
        drive = Storage.get_storage_by_name(name)
        if drive:
            return drive.specs.get("read_speed")
        return None

    @staticmethod
    def get_storage_write_speed(name):
        drive = Storage.get_storage_by_name(name)
        if drive:
            return drive.specs.get("write_speed")
        return None
