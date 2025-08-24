"""
Base service class for all services in the Wild Ginger Event Management System.
Provides common functionality and interface for all services.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import logging


class BaseService(ABC):
    """Base class for all services in the system."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize the base service with optional logger."""
        self.logger = logger or logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the service and its dependencies."""
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Clean up resources when shutting down the service."""
        pass
    
    def log_info(self, message: str, **kwargs: Any) -> None:
        """Log an info message with optional context."""
        self.logger.info(message, extra=kwargs)
    
    def log_error(self, message: str, **kwargs: Any) -> None:
        """Log an error message with optional context."""
        self.logger.error(message, extra=kwargs)
    
    def log_warning(self, message: str, **kwargs: Any) -> None:
        """Log a warning message with optional context."""
        self.logger.warning(message, extra=kwargs) 