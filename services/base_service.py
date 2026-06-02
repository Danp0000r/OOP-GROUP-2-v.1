"""
BASE SERVICE - Abstract Base Class for All Services
Demonstrates: ABSTRACTION & POLYMORPHISM

This abstract base class defines the contract that all services must follow.
It encapsulates common service behavior and provides a consistent interface.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseService(ABC):
    """
    Abstract base service class implementing the Strategy pattern.
    
    Pillars demonstrated:
    - ABSTRACTION: Defines interface without implementation details
    - POLYMORPHISM: Subclasses implement execute() differently
    - ENCAPSULATION: Protected methods for shared logic
    """
    
    def __init__(self):
        """Initialize base service."""
        self._cache = {}
        self._error_log = []
    
    @abstractmethod
    def execute(self, *args, **kwargs) -> Any:
        """
        Execute the service logic. Must be implemented by subclasses.
        
        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Result of service execution
        """
        pass
    
    def _log_error(self, error_msg: str, context: Optional[Dict] = None) -> None:
        """
        Protected method: Log errors internally (ENCAPSULATION).
        
        Args:
            error_msg: Error message
            context: Additional error context
        """
        error_record = {
            "message": error_msg,
            "context": context or {}
        }
        self._error_log.append(error_record)
    
    def _cache_result(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Protected method: Cache results (ENCAPSULATION).
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live (not enforced, for future use)
        """
        self._cache[key] = value
    
    def _get_cached(self, key: str) -> Optional[Any]:
        """
        Protected method: Retrieve cached value (ENCAPSULATION).
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
        return self._cache.get(key)
    
    def get_errors(self) -> List[Dict]:
        """Get all logged errors."""
        return self._error_log.copy()
    
    def clear_errors(self) -> None:
        """Clear error log."""
        self._error_log.clear()
    
    def clear_cache(self) -> None:
        """Clear service cache."""
        self._cache.clear()


class DataAccessService(BaseService):
    """
    Abstract service for data access operations.
    Demonstrates: INHERITANCE & POLYMORPHISM
    
    Subclasses handle specific data models.
    """
    
    @abstractmethod
    def get_all(self, *args, **kwargs) -> List[Any]:
        """Retrieve all entities."""
        pass
    
    @abstractmethod
    def get_by_id(self, entity_id: Any) -> Optional[Any]:
        """Retrieve single entity by ID."""
        pass
    
    @abstractmethod
    def create(self, data: Dict) -> Any:
        """Create new entity."""
        pass
    
    @abstractmethod
    def update(self, entity_id: Any, data: Dict) -> Optional[Any]:
        """Update existing entity."""
        pass
    
    @abstractmethod
    def delete(self, entity_id: Any) -> bool:
        """Delete entity."""
        pass


class BusinessLogicService(BaseService):
    """
    Abstract service for business logic operations.
    Demonstrates: INHERITANCE & ABSTRACTION
    
    Subclasses implement domain-specific logic.
    """
    
    def validate_input(self, data: Dict, required_fields: List[str]) -> bool:
        """
        Protected helper: Validate input data (ENCAPSULATION).
        
        Args:
            data: Input data dict
            required_fields: List of required field names
            
        Returns:
            True if all required fields present, False otherwise
        """
        for field in required_fields:
            if field not in data or data[field] is None:
                self._log_error(f"Missing required field: {field}")
                return False
        return True
    
    def sanitize_data(self, data: Dict) -> Dict:
        """
        Protected helper: Sanitize data (ENCAPSULATION).
        
        Args:
            data: Raw data dictionary
            
        Returns:
            Sanitized data dictionary
        """
        return {k: str(v).strip() if isinstance(v, str) else v 
                for k, v in data.items()}
