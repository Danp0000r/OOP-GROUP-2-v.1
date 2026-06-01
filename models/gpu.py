from models.component import Component


class GPU:

    @staticmethod
    def get_all_gpus():

        return Component.query.filter_by(
            category="GPU"
        ).all()

    @staticmethod
    def get_gpu_by_name(name):

        return Component.query.filter_by(
            category="GPU",
            name=name
        ).first()

    @staticmethod
    def get_gpus_by_brand(brand):

        return Component.query.filter_by(
            category="GPU",
            brand=brand
        ).all()

    @staticmethod
    def get_gpus_by_vram(vram):

        gpus = GPU.get_all_gpus()

        return [

            gpu for gpu in gpus

            if gpu.specs.get("vram") == vram

        ]

    @staticmethod
    def get_gpus_by_chipset(chipset):

        gpus = GPU.get_all_gpus()

        return [

            gpu for gpu in gpus

            if gpu.specs.get("chipset") == chipset

        ]

    @staticmethod
    def get_gpus_by_interface(interface):

        gpus = GPU.get_all_gpus()

        return [

            gpu for gpu in gpus

            if gpu.specs.get("interface") == interface

        ]

    @staticmethod
    def get_gpu_tdp(name):

        gpu = GPU.get_gpu_by_name(name)

        if gpu:

            return gpu.specs.get("tdp")

        return None

    @staticmethod
    def get_gpu_length(name):

        gpu = GPU.get_gpu_by_name(name)

        if gpu:

            return gpu.specs.get("length_mm")

        return None

    @staticmethod
    def get_gpu_vram(name):

        gpu = GPU.get_gpu_by_name(name)

        if gpu:

            return gpu.specs.get("vram")

        return None

    @staticmethod
    def get_gpu_interface(name):

        gpu = GPU.get_gpu_by_name(name)

        if gpu:

            return gpu.specs.get("interface")

        return None