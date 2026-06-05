from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseService(ABC):

    def __init__(self):
        self._cache = {}
        self._error_log = []

    @abstractmethod
    def execute(self, *args, **kwargs) -> Any:
        pass

    def _log_error(self, error_msg: str, context: Optional[Dict] = None) -> None:
        error_record = {"message": error_msg, "context": context or {}}
        self._error_log.append(error_record)

    def _cache_result(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        self._cache[key] = value

    def _get_cached(self, key: str) -> Optional[Any]:
        return self._cache.get(key)

    def get_errors(self) -> List[Dict]:
        return self._error_log.copy()

    def clear_errors(self) -> None:
        self._error_log.clear()

    def clear_cache(self) -> None:
        self._cache.clear()


class DataAccessService(BaseService):

    @abstractmethod
    def get_all(self, *args, **kwargs) -> List[Any]:
        pass

    @abstractmethod
    def get_by_id(self, entity_id: Any) -> Optional[Any]:
        pass

    @abstractmethod
    def create(self, data: Dict) -> Any:
        pass

    @abstractmethod
    def update(self, entity_id: Any, data: Dict) -> Optional[Any]:
        pass

    @abstractmethod
    def delete(self, entity_id: Any) -> bool:
        pass


class BusinessLogicService(BaseService):

    def validate_input(self, data: Dict, required_fields: List[str]) -> bool:
        for field in required_fields:
            if field not in data or data[field] is None:
                self._log_error(f"Missing required field: {field}")
                return False
        return True

    def sanitize_data(self, data: Dict) -> Dict:
        return {k: str(v).strip() if isinstance(v, str) else v for k, v in data.items()}
