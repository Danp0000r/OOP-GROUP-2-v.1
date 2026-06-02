"""
COMPONENT SPECS - Specification Accessor Class
Demonstrates: ENCAPSULATION

Type-safe access to component specifications with default values.
Hides the internal dictionary structure and provides clean interface.
"""

from typing import Any, Dict, Optional, Union


class ComponentSpecs:
    """
    Encapsulates component specifications with type-safe access.
    
    Pillars demonstrated:
    - ENCAPSULATION: Hides internal dict, provides clean interface
    - ABSTRACTION: Presents specs as properties, not raw dict access
    
    Usage:
        specs = ComponentSpecs({"wattage": 750, "efficiency": "80+Bronze"})
        print(specs.wattage)  # 750
        print(specs.get("unknown", 0))  # 0
    """
    
    def __init__(self, specs_dict: Optional[Dict[str, Any]] = None):
        """
        Initialize specs from dictionary.
        
        Args:
            specs_dict: Dictionary of specifications
        """
        self._specs = specs_dict or {}
    
    @property
    def raw(self) -> Dict[str, Any]:
        """Get raw specs dictionary (read-only copy)."""
        return self._specs.copy()
    
    def get(self, key: str, default: Any = None) -> Any:
        """Safe get with default value."""
        return self._specs.get(key, default)
    
    def has(self, key: str) -> bool:
        """Check if spec exists."""
        return key in self._specs
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return self._specs.copy()
    
    def __getitem__(self, key: str) -> Any:
        """Dictionary-like access."""
        return self._specs[key]
    
    def __contains__(self, key: str) -> bool:
        """Support 'in' operator."""
        return key in self._specs
    
    def __repr__(self) -> str:
        return f"ComponentSpecs({self._specs})"


class CPUSpecs(ComponentSpecs):
    """
    Specialized specs for CPU components.
    
    Demonstrates: INHERITANCE & POLYMORPHISM
    CPU-specific properties with defaults.
    """
    
    @property
    def cores(self) -> int:
        """Number of cores."""
        return self.get("cores", 0)
    
    @property
    def threads(self) -> int:
        """Number of threads."""
        return self.get("threads", 0)
    
    @property
    def socket(self) -> str:
        """CPU socket type."""
        return self.get("socket", "Unknown")
    
    @property
    def base_clock(self) -> float:
        """Base clock speed in GHz."""
        return self.get("base_clock", 0.0)
    
    @property
    def boost_clock(self) -> float:
        """Boost clock speed in GHz."""
        return self.get("boost_clock", 0.0)
    
    @property
    def tdp(self) -> int:
        """Thermal Design Power in watts."""
        return self.get("tdp", 0)


class GPUSpecs(ComponentSpecs):
    """
    Specialized specs for GPU components.
    
    Demonstrates: INHERITANCE & POLYMORPHISM
    GPU-specific properties with defaults.
    """
    
    @property
    def vram(self) -> int:
        """VRAM in GB."""
        return self.get("vram", 0)
    
    @property
    def vram_type(self) -> str:
        """VRAM type (GDDR6, GDDR6X, HBM, etc)."""
        return self.get("vram_type", "Unknown")
    
    @property
    def chipset(self) -> str:
        """GPU chipset/architecture."""
        return self.get("chipset", "Unknown")
    
    @property
    def memory_bus(self) -> int:
        """Memory bus width in bits."""
        return self.get("memory_bus", 0)
    
    @property
    def tdp(self) -> int:
        """Power consumption in watts."""
        return self.get("tdp", 0)
    
    @property
    def ray_tracing(self) -> bool:
        """Supports ray tracing."""
        return self.get("ray_tracing", False)


class RAMSpecs(ComponentSpecs):
    """
    Specialized specs for RAM components.
    
    Demonstrates: INHERITANCE & POLYMORPHISM
    RAM-specific properties with defaults.
    """
    
    @property
    def capacity(self) -> int:
        """RAM capacity in GB."""
        return self.get("capacity", 0)
    
    @property
    def type(self) -> str:
        """RAM type (DDR4, DDR5, etc)."""
        return self.get("type", "Unknown")
    
    @property
    def speed(self) -> int:
        """RAM speed in MHz."""
        return self.get("speed", 0)
    
    @property
    def cas_latency(self) -> int:
        """CAS latency."""
        return self.get("cas_latency", 0)


class StorageSpecs(ComponentSpecs):
    """
    Specialized specs for Storage components.
    
    Demonstrates: INHERITANCE & POLYMORPHISM
    Storage-specific properties with defaults.
    """
    
    @property
    def capacity(self) -> int:
        """Storage capacity in GB."""
        return self.get("capacity", 0)
    
    @property
    def type(self) -> str:
        """Storage type (SSD, HDD, NVMe, etc)."""
        return self.get("type", "Unknown")
    
    @property
    def interface(self) -> str:
        """Interface type (SATA, M.2, NVMe, etc)."""
        return self.get("interface", "Unknown")
    
    @property
    def read_speed(self) -> int:
        """Read speed in MB/s."""
        return self.get("read_speed", 0)
    
    @property
    def write_speed(self) -> int:
        """Write speed in MB/s."""
        return self.get("write_speed", 0)


class PSUSpecs(ComponentSpecs):
    """
    Specialized specs for PSU components.
    
    Demonstrates: INHERITANCE & POLYMORPHISM
    PSU-specific properties with defaults.
    """
    
    @property
    def wattage(self) -> int:
        """Power supply wattage."""
        return self.get("wattage", 0)
    
    @property
    def efficiency(self) -> str:
        """Efficiency rating (80+Bronze, 80+Gold, etc)."""
        return self.get("efficiency", "Unrated")
    
    @property
    def modular(self) -> str:
        """Modular type (Full, Semi, Non)."""
        return self.get("modular", "Non")
    
    @property
    def form_factor(self) -> str:
        """Form factor (ATX, SFX, etc)."""
        return self.get("form_factor", "Unknown")


class MotherboardSpecs(ComponentSpecs):
    """
    Specialized specs for Motherboard components.
    
    Demonstrates: INHERITANCE & POLYMORPHISM
    Motherboard-specific properties with defaults.
    """
    
    @property
    def socket_type(self) -> str:
        """CPU socket type."""
        return self.get("socket_type", "Unknown")
    
    @property
    def ram_type(self) -> str:
        """Supported RAM type."""
        return self.get("ram_type", "Unknown")
    
    @property
    def max_ram(self) -> int:
        """Maximum RAM capacity in GB."""
        return self.get("max_ram", 0)
    
    @property
    def form_factor(self) -> str:
        """Form factor (ATX, Micro-ATX, Mini-ITX, etc)."""
        return self.get("form_factor", "Unknown")


class CoolingSpecs(ComponentSpecs):
    """
    Specialized specs for Cooling components.
    
    Demonstrates: INHERITANCE & POLYMORPHISM
    Cooling-specific properties with defaults.
    """
    
    @property
    def type(self) -> str:
        """Cooling type (Air, Liquid, Passive, etc)."""
        return self.get("type", "Unknown")
    
    @property
    def tdp_rating(self) -> int:
        """TDP rating in watts."""
        return self.get("tdp_rating", 0)
    
    @property
    def height(self) -> int:
        """Height in mm."""
        return self.get("height", 0)
    
    @property
    def socket_compatibility(self) -> list:
        """List of compatible sockets."""
        return self.get("socket_compatibility", [])


class CaseSpecs(ComponentSpecs):
    """
    Specialized specs for Case components.
    
    Demonstrates: INHERITANCE & POLYMORPHISM
    Case-specific properties with defaults.
    """
    
    @property
    def form_factor(self) -> str:
        """Supported motherboard form factor."""
        return self.get("form_factor", "Unknown")
    
    @property
    def gpu_length_limit(self) -> int:
        """Maximum GPU length in mm."""
        return self.get("gpu_length_limit", 0)
    
    @property
    def cpu_cooler_height_limit(self) -> int:
        """Maximum CPU cooler height in mm."""
        return self.get("cpu_cooler_height_limit", 0)
