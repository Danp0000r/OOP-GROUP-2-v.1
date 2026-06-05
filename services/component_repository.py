
from typing import List, Optional, Dict, Any
from functools import lru_cache
from models.component import Component
from models.base_component import ComponentFactory, BaseComponent


class ComponentRepository:
    
    def __init__(self):
        self._cache = {}
    
    def get_all(self) -> List[BaseComponent]:
        components = Component.query.all()
        return [ComponentFactory.create(c) for c in components]
    
    def get_by_id(self, component_id: int) -> Optional[BaseComponent]:
        component = Component.query.get(component_id)
        return ComponentFactory.create(component) if component else None
    
    def get_by_name(self, name: str) -> Optional[BaseComponent]:
        component = Component.query.filter_by(name=name).first()
        return ComponentFactory.create(component) if component else None
    
    def get_by_category(self, category: str) -> List[BaseComponent]:
        components = Component.query.filter_by(category=category).all()
        return [ComponentFactory.create(c) for c in components]
    
    def search_by_name(self, search_term: str) -> List[BaseComponent]:
        components = Component.query.filter(
            Component.name.ilike(f"%{search_term}%")
        ).all()
        return [ComponentFactory.create(c) for c in components]
    
    def search_by_brand(self, brand: str) -> List[BaseComponent]:
        components = Component.query.filter_by(brand=brand).all()
        return [ComponentFactory.create(c) for c in components]
    
    def get_by_price_range(self, min_price: float, max_price: float) -> List[BaseComponent]:
        components = Component.query.filter(
            Component.price >= min_price,
            Component.price <= max_price
        ).all()
        return [ComponentFactory.create(c) for c in components]
    
    def get_by_spec(self, category: str, spec_key: str, spec_value: Any) -> List[BaseComponent]:
        components = self.get_by_category(category)
        return [
            c for c in components 
            if c.specs.get(spec_key) == spec_value
        ]
    
    def get_cpus(self) -> List[BaseComponent]:
        return self.get_by_category("CPU")
    
    def get_cpus_by_socket(self, socket: str) -> List[BaseComponent]:
        return self.get_by_spec("CPU", "socket", socket)
    
    def get_cpus_by_cores(self, cores: int) -> List[BaseComponent]:
        return self.get_by_spec("CPU", "cores", cores)
    
    def get_gpus(self) -> List[BaseComponent]:
        return self.get_by_category("GPU")
    
    def get_gpus_by_vram(self, vram_gb: int) -> List[BaseComponent]:
        return self.get_by_spec("GPU", "vram", vram_gb)
    
    def get_ram(self) -> List[BaseComponent]:
        return self.get_by_category("RAM")
    
    def get_ram_by_capacity(self, capacity_gb: int) -> List[BaseComponent]:
        return self.get_by_spec("RAM", "capacity", capacity_gb)
    
    def get_ram_by_type(self, ram_type: str) -> List[BaseComponent]:
        return self.get_by_spec("RAM", "type", ram_type)
    
    def get_storage(self) -> List[BaseComponent]:
        return self.get_by_category("Storage")
    
    def get_storage_by_type(self, storage_type: str) -> List[BaseComponent]:
        return self.get_by_spec("Storage", "type", storage_type)
    
    def get_psus(self) -> List[BaseComponent]:
        return self.get_by_category("PSU")
    
    def get_psus_by_wattage(self, wattage: int) -> List[BaseComponent]:
        return self.get_by_spec("PSU", "wattage", wattage)
    
    def get_motherboards(self) -> List[BaseComponent]:
        return self.get_by_category("Motherboard")
    
    def get_motherboards_by_socket(self, socket: str) -> List[BaseComponent]:
        return self.get_by_spec("Motherboard", "socket_type", socket)
    
    def get_cooling(self) -> List[BaseComponent]:
        return self.get_by_category("Cooling")
    
    def get_cases(self) -> List[BaseComponent]:
        return self.get_by_category("Case")
    
    def _clear_cache(self) -> None:
        self._cache.clear()
    
    def _get_or_cache(self, key: str, factory_fn):
        if key not in self._cache:
            self._cache[key] = factory_fn()
        return self._cache[key]


# Singleton instance (common pattern for repositories)
_repository_instance = None


def get_component_repository() -> ComponentRepository:
    global _repository_instance
    if _repository_instance is None:
        _repository_instance = ComponentRepository()
    return _repository_instance
