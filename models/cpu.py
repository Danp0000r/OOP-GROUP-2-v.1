from models.component import Component


class CPU:

    @staticmethod
    def get_all_cpus():

        return Component.query.filter_by(
            category="CPU"
        ).all()

    @staticmethod
    def get_cpu_by_name(name):

        return Component.query.filter_by(
            category="CPU",
            name=name
        ).first()

    @staticmethod
    def get_cpus_by_brand(brand):

        return Component.query.filter_by(
            category="CPU",
            brand=brand
        ).all()

    @staticmethod
    def get_cpus_by_socket(socket):

        cpus = CPU.get_all_cpus()

        return [

            cpu for cpu in cpus

            if cpu.specs.get("socket") == socket

        ]

    @staticmethod
    def get_cpus_by_core_count(core_count):

        cpus = CPU.get_all_cpus()

        return [

            cpu for cpu in cpus

            if cpu.specs.get("cores") == core_count

        ]

    @staticmethod
    def get_cpu_socket(name):

        cpu = CPU.get_cpu_by_name(name)

        if cpu:

            return cpu.specs.get("socket")

        return None

    @staticmethod
    def get_cpu_cores(name):

        cpu = CPU.get_cpu_by_name(name)

        if cpu:

            return cpu.specs.get("cores")

        return None

    @staticmethod
    def get_cpu_threads(name):

        cpu = CPU.get_cpu_by_name(name)

        if cpu:

            return cpu.specs.get("threads")

        return None

    @staticmethod
    def get_cpu_base_clock(name):

        cpu = CPU.get_cpu_by_name(name)

        if cpu:

            return cpu.specs.get("base_clock")

        return None

    @staticmethod
    def get_cpu_tdp(name):

        cpu = CPU.get_cpu_by_name(name)

        if cpu:

            return cpu.specs.get("tdp")

        return None

    @staticmethod
    def has_integrated_graphics(name):

        cpu = CPU.get_cpu_by_name(name)

        if cpu:

            return cpu.specs.get("integrated_graphics")

        return None