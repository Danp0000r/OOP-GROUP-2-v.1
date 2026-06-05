
from abc import abstractmethod
from typing import Dict, List, Optional, Any
from models.component_specs import ComponentSpecs


class BaseComponent:

    # Class variable: Category name (overridden in subclasses)
    CATEGORY = "UNKNOWN"

    def __init__(self, component_obj=None):

        self._component = component_obj
        self._specs = None

    @property
    def specs(self) -> ComponentSpecs:
        """Get component specs with type-safe access."""
        if self._specs is None and self._component:
            self._specs = self._create_specs_object(self._component.specs or {})
        return self._specs or ComponentSpecs({})

    @abstractmethod
    def _create_specs_object(self, specs_dict: Dict) -> ComponentSpecs:
        """
        Create appropriate specs object for this component type.
        Implemented by subclasses.

        Args:
            specs_dict: Raw specs dictionary

        Returns:
            Specialized ComponentSpecs subclass
        """
        pass

    def to_dict(self) -> Dict[str, Any]:
        """Convert component to dictionary."""
        if not self._component:
            return {}

        return {
            "component_id": self._component.component_id,
            "name": self._component.name,
            "category": self._component.category,
            "brand": self._component.brand,
            "specs": self.specs.to_dict(),
            "price": self._component.price,
            "performance_score": self._component.performance_score,
            "image_url": self._component.image_url,
            "description": self._component.description,
        }

    def __repr__(self) -> str:
        name = self._component.name if self._component else "Unknown"
        return f"{self.__class__.__name__}({name})"


class CPUComponent(BaseComponent):
    """CPU component type. Demonstrates INHERITANCE & POLYMORPHISM."""

    CATEGORY = "CPU"

    def _create_specs_object(self, specs_dict: Dict) -> ComponentSpecs:
        from models.component_specs import CPUSpecs

        return CPUSpecs(specs_dict)


class GPUComponent(BaseComponent):
    """GPU component type. Demonstrates INHERITANCE & POLYMORPHISM."""

    CATEGORY = "GPU"

    def _create_specs_object(self, specs_dict: Dict) -> ComponentSpecs:
        from models.component_specs import GPUSpecs

        return GPUSpecs(specs_dict)


class RAMComponent(BaseComponent):
    """RAM component type. Demonstrates INHERITANCE & POLYMORPHISM."""

    CATEGORY = "RAM"

    def _create_specs_object(self, specs_dict: Dict) -> ComponentSpecs:
        from models.component_specs import RAMSpecs

        return RAMSpecs(specs_dict)


class StorageComponent(BaseComponent):
    """Storage component type. Demonstrates INHERITANCE & POLYMORPHISM."""

    CATEGORY = "Storage"

    def _create_specs_object(self, specs_dict: Dict) -> ComponentSpecs:
        from models.component_specs import StorageSpecs

        return StorageSpecs(specs_dict)


class PSUComponent(BaseComponent):
    """PSU component type. Demonstrates INHERITANCE & POLYMORPHISM."""

    CATEGORY = "PSU"

    def _create_specs_object(self, specs_dict: Dict) -> ComponentSpecs:
        from models.component_specs import PSUSpecs

        return PSUSpecs(specs_dict)


class MotherboardComponent(BaseComponent):
    """Motherboard component type. Demonstrates INHERITANCE & POLYMORPHISM."""

    CATEGORY = "Motherboard"

    def _create_specs_object(self, specs_dict: Dict) -> ComponentSpecs:
        from models.component_specs import MotherboardSpecs

        return MotherboardSpecs(specs_dict)


class CoolingComponent(BaseComponent):
    """Cooling component type. Demonstrates INHERITANCE & POLYMORPHISM."""

    CATEGORY = "Cooling"

    def _create_specs_object(self, specs_dict: Dict) -> ComponentSpecs:
        from models.component_specs import CoolingSpecs

        return CoolingSpecs(specs_dict)


class CaseComponent(BaseComponent):
    """Case component type. Demonstrates INHERITANCE & POLYMORPHISM."""

    CATEGORY = "Case"

    def _create_specs_object(self, specs_dict: Dict) -> ComponentSpecs:
        from models.component_specs import CaseSpecs

        return CaseSpecs(specs_dict)


# Factory for creating component wrapper objects
class ComponentFactory:
    """
    Factory pattern for creating appropriate component wrappers.

    Demonstrates: POLYMORPHISM & ABSTRACTION

    Usage:
        cpu_obj = Component.query.filter_by(category="CPU").first()
        cpu_wrapper = ComponentFactory.create(cpu_obj)
        print(cpu_wrapper.specs.cores)  # Type-safe access
    """

    _COMPONENT_MAP = {
        "CPU": CPUComponent,
        "GPU": GPUComponent,
        "RAM": RAMComponent,
        "Storage": StorageComponent,
        "PSU": PSUComponent,
        "Motherboard": MotherboardComponent,
        "Cooling": CoolingComponent,
        "Case": CaseComponent,
    }

    @classmethod
    def create(cls, component_obj) -> BaseComponent:
        """
        Create appropriate component wrapper based on category.

        Args:
            component_obj: SQLAlchemy Component instance

        Returns:
            Appropriate BaseComponent subclass instance
        """
        if not component_obj:
            return BaseComponent(component_obj)

        category = component_obj.category
        component_class = cls._COMPONENT_MAP.get(category, BaseComponent)
        return component_class(component_obj)

    @classmethod
    def register(cls, category: str, component_class: type) -> None:
        """
        Register a new component type (extensibility).

        Demonstrates: POLYMORPHISM

        Args:
            category: Category name
            component_class: Component class (must inherit from BaseComponent)
        """
        if not issubclass(component_class, BaseComponent):
            raise TypeError(f"{component_class} must inherit from BaseComponent")
        cls._COMPONENT_MAP[category] = component_class
