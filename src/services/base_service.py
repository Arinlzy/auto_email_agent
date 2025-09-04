from abc import ABC, abstractmethod
from typing import Any, Dict
from ..config.model_configs import ModelConfigManager

class BaseService(ABC):
    """Base class for all services"""
    
    def __init__(self, config_manager: ModelConfigManager = None):
        self.config_manager = config_manager or ModelConfigManager()
    
    @abstractmethod
    def initialize(self):
        """Initialize the service"""
        pass
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get service information"""
        return {
            "service_name": self.__class__.__name__,
            "config_manager": str(self.config_manager)
        }