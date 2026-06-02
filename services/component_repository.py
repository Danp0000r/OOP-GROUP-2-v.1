"""
COMPONENT REPOSITORY - Data Access Abstraction Layer
Demonstrates: ABSTRACTION, ENCAPSULATION, POLYMORPHISM

Repository pattern provides clean separation between data access and business logic.
Hides SQLAlchemy details behind a consistent interface.
"""

from typing import List, Optional, Dict, Any
from functools import lru_cache
from models.component import Component
from models.base_component import ComponentFactory, BaseComponent


class ComponentRepository:
    """
    Repository for component data access.
    
    Pillars demonstrated:
    - ABSTRACTION: Hides SQLAlchemy queries
    - ENCAPSULATION: All component queries go through this
    - POLYMORPHISM: Multiple filter methods with consistent interface
    
    Usage:
        repo = ComponentRepository()
        cpus = repo.get_by_category("CPU")
        gpu = repo.get_by_id(42)
    """
    
    def __init__(self):
        """Initialize repository with cache."""
        self._cache = {}
    
    # ─── Public interface (ABSTRACTION) ───────────────────────
    
    def get_all(self) -> List[BaseComponent]:
        """Get all components."""
        components = Component.query.all()
        return [ComponentFactory.create(c) for c in components]
    
    def get_by_id(self, component_id: int) -> Optional[BaseComponent]:
        """Get component by ID."""
        component = Component.query.get(component_id)
        return ComponentFactory.create(component) if component else None
    
    def get_by_name(self, name: str) -> Optional[BaseComponent]:
        """Get component by exact name."""
        component = Component.query.filter_by(name=name).first()
        return ComponentFactory.create(component) if component else None
    
    def get_by_category(self, category: str) -> List[BaseComponent]:
        """Get all components in a category."""
        components = Component.query.filter_by(category=category).all()
        return [ComponentFactory.create(c) for c in components]
    
    def search_by_name(self, search_term: str) -> List[BaseComponent]:
        """Search components by name (substring match)."""
        components = Component.query.filter(
            Component.name.ilike(f"%{search_term}%")
        ).all()
        return [ComponentFactory.create(c) for c in components]
    
    def search_by_brand(self, brand: str) -> List[BaseComponent]:
        """Get components by brand."""
        components = Component.query.filter_by(brand=brand).all()
        return [ComponentFactory.create(c) for c in components]
    
    def get_by_price_range(self, min_price: float, max_price: float) -> List[BaseComponent]:
        """Get components within price range."""
        components = Component.query.filter(
            Component.price >= min_price,
            Component.price <= max_price
        ).all()
        return [ComponentFactory.create(c) for c in components]
    
    def get_by_spec(self, category: str, spec_key: str, spec_value: Any) -> List[BaseComponent]:
        """
        Get components by specification value.
        
        Args:
            category: Component category
            spec_key: Specification key
            spec_value: Specification value to match
            
        Returns:
            List of matching components
        """
        components = self.get_by_category(category)
        return [
            c for c in components 
            if c.specs.get(spec_key) == spec_value
        ]
    
    # ─── Category-specific methods (POLYMORPHISM) ─────────────
    
    def get_cpus(self) -> List[BaseComponent]:
        """Get all CPUs."""
        return self.get_by_category("CPU")
    
    def get_cpus_by_socket(self, socket: str) -> List[BaseComponent]:
        """Get CPUs by socket type."""
        return self.get_by_spec("CPU", "socket", socket)
    
    def get_cpus_by_cores(self, cores: int) -> List[BaseComponent]:
        """Get CPUs by core count."""
        return self.get_by_spec("CPU", "cores", cores)
    
    def get_gpus(self) -> List[BaseComponent]:
        """Get all GPUs."""
        return self.get_by_category("GPU")
    
    def get_gpus_by_vram(self, vram_gb: int) -> List[BaseComponent]:
        """Get GPUs by VRAM amount."""
        return self.get_by_spec("GPU", "vram", vram_gb)
    
    def get_ram(self) -> List[BaseComponent]:
        """Get all RAM."""
        return self.get_by_category("RAM")
    
    def get_ram_by_capacity(self, capacity_gb: int) -> List[BaseComponent]:
        """Get RAM by capacity."""
        return self.get_by_spec("RAM", "capacity", capacity_gb)
    
    def get_ram_by_type(self, ram_type: str) -> List[BaseComponent]:
        """Get RAM by type (DDR4, DDR5, etc)."""
        return self.get_by_spec("RAM", "type", ram_type)
    
    def get_storage(self) -> List[BaseComponent]:
        """Get all storage."""
        return self.get_by_category("Storage")
    
    def get_storage_by_type(self, storage_type: str) -> List[BaseComponent]:
        """Get storage by type (SSD, HDD, NVMe, etc)."""
        return self.get_by_spec("Storage", "type", storage_type)
    
    def get_psus(self) -> List[BaseComponent]:
        """Get all PSUs."""
        return self.get_by_category("PSU")
    
    def get_psus_by_wattage(self, wattage: int) -> List[BaseComponent]:
        """Get PSUs by wattage."""
        return self.get_by_spec("PSU", "wattage", wattage)
    
    def get_motherboards(self) -> List[BaseComponent]:
        """Get all motherboards."""
        return self.get_by_category("Motherboard")
    
    def get_motherboards_by_socket(self, socket: str) -> List[BaseComponent]:
        """Get motherboards by socket type."""
        return self.get_by_spec("Motherboard", "socket_type", socket)
    
    def get_cooling(self) -> List[BaseComponent]:
        """Get all cooling solutions."""
        return self.get_by_category("Cooling")
    
    def get_cases(self) -> List[BaseComponent]:
        """Get all cases."""
        return self.get_by_category("Case")
    
    # ─── Protected helper methods (ENCAPSULATION) ─────────────
    
    def _clear_cache(self) -> None:
        """Clear internal cache."""
        self._cache.clear()
    
    def _get_or_cache(self, key: str, factory_fn):
        """Get value from cache or compute and cache."""
        if key not in self._cache:
            self._cache[key] = factory_fn()
        return self._cache[key]


# Singleton instance (common pattern for repositories)
_repository_instance = None


def get_component_repository() -> ComponentRepository:
    """
    Get singleton instance of ComponentRepository.
    
    Demonstrates: ENCAPSULATION & ABSTRACTION
    
    Returns:
        ComponentRepository instance
    """
    global _repository_instance
    if _repository_instance is None:
        _repository_instance = ComponentRepository()
    return _repository_instance
